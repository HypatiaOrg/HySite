#!/bin/bash
# HySite update job: newest versions -> test -> deploy -> record.
#
# Run weekly on the production server by deploy/systemd/hysite-update.timer, or now with
# scripts/update.sh. Settings come from /etc/hysite/update.env (deploy/systemd/update.env.example).
#
#  1. Update the code: fast-forward to origin/$HYSITE_BRANCH.
#  2. Resolve the newest versions: scripts/refresh_versions.py writes versions.env and the
#     requirements.lock files (ignored by git).
#  3. Stop here if neither the code, nor any version, nor one of the other sites' checkouts changed.
#  4. Test: build and run the whole site against the sample database (compose.test.yaml)
#     and run the smoke tests; build the other sites' images on the tested nginx. On failure: put the
#     previous versions back, stop.
#  5. Deploy: rebuild production from the tested versions and recreate changed containers,
#     keeping the old images as :previous. The nginx of the other sites on this server (the HTTPS
#     edge in HyRoute, the CWSite page; their compose files are listed in HYSITE_NGINX_COMPOSE) is
#     recreated with the same tested NGINX_IMAGE, or with the image built on it in step 4. Smoke test
#     production and check that every one of those sites answers. On failure: roll back, them
#     included (a site's checkout goes back to the commit deployed before).
#  6. Every step is recorded in the hysite_ops.deployments collection (scripts/deployments.py).
#  7. A report of the run is emailed to HYSITE_REPORT_EMAIL, if set (scripts/send_report.py).
#
# Exits non-zero on any failure, so systemd starts hysite-alert@ to send an email.
#
# Settings all start with HYSITE_, OPS_ or ALERT_. Docker Compose gives environment variables
# priority over .env files, so a setting such as MONGO_HOST here would silently change the
# website's (and the test stack's) database. Never add variables that compose.yaml uses.
set -uo pipefail

REPO=${HYSITE_REPO:-/home/ubuntu/HySite}
BRANCH=${HYSITE_BRANCH:-main}
# false skips step 1, for testing changes that are not pushed yet
GIT_UPDATE=${HYSITE_GIT_UPDATE:-true}
PROD_URL=${HYSITE_URL:-http://localhost}
# compose files of the other sites on this server whose "nginx" service runs the NGINX_IMAGE tested here:
# the HTTPS edge (HyRoute) and the CWSite page, whose nginx is built on it (its Dockerfile adds the site).
# Space-separated; a file that is absent is skipped.
# HYSITE_EDGE_COMPOSE is the older name for the edge alone and still works.
NGINX_COMPOSE=${HYSITE_NGINX_COMPOSE:-/home/ubuntu/HyRoute/compose.yaml /home/ubuntu/CWSite/compose.yaml}
NGINX_COMPOSE="${HYSITE_EDGE_COMPOSE:-} $NGINX_COMPOSE"
# addresses of those sites that must answer 200 after a deploy (space-separated; production itself
# has the smoke test). Empty: only check that their containers run
NGINX_CHECK_URLS=${HYSITE_NGINX_CHECK_URLS:-}
TEST_URL=http://localhost:8081
# seconds the smoke test waits for a site to start
SMOKE_WAIT=${HYSITE_SMOKE_WAIT:-300}
# the backend image has pymongo, so it runs scripts/deployments.py
OPS_IMAGE=${OPS_IMAGE:-hysite-django-api:latest}
OPS_NETWORK=${OPS_NETWORK:-hynet}
BUILT_IMAGES=(hysite-django-api hysite-web-to-py)
PINNED_FILES=(versions.env backend/requirements.lock frontend-web2py/requirements.lock)
KEEP_RUNS=20

cd "$REPO" || exit 1
# refuse to run if the environment would override .env or test.env (see the note above)
for variable in $(grep -oE '\$\{[A-Z_]+' compose.yaml | tr -d '${' | sort -u); do
    if [ -n "${!variable+set}" ]; then
        echo "$variable is set in the environment and would override .env and test.env; unset it"
        exit 1
    fi
done
mkdir -p .update/runs .update/backup
# only one update at a time
exec 9> .update/lock
flock --nonblock 9 || { echo "Another update is already running"; exit 1; }

RUN_ID=$(date -u +%Y-%m-%dT%H-%M-%SZ)
RUN_DIR=.update/runs/$RUN_ID
mkdir -p "$RUN_DIR"
RECORD_FAILED=false

log() { echo "[$(date -u +%H:%M:%S)] $*"; }

# the production stack, built from the tested versions
prod_compose() { COMPOSE_ENV_FILES=.env,versions.env docker compose "$@"; }
# the test stack: its own project, network and port, with the sample database
test_compose() {
    COMPOSE_PROJECT_NAME=hysite-test COMPOSE_FILE=compose.yaml:compose.test.yaml \
        COMPOSE_ENV_FILES=test.env,versions.env docker compose "$@"
}

# another site's compose file ($1): its own .env (if any), then versions.env, which sets NGINX_IMAGE
nginx_compose() {
    local file=$1 env_files="$REPO/versions.env"
    shift
    [ -f "$(dirname "$file")/.env" ] && env_files="$(dirname "$file")/.env,$env_files"
    COMPOSE_ENV_FILES=$env_files docker compose --file "$file" "$@"
}
# The other sites on this server: HyRoute (the HTTPS edge) and CWSite. Each has a compose file with an
# "nginx" service on ${NGINX_IMAGE}, as the image or as the base of a build. Their code arrives by a
# git push from the owner's computer into the checkout (README of each); this job never pulls them.
# the compose files that are on this server, each once (a file can be listed twice: HYSITE_EDGE_COMPOSE
# and the default)
site_files() {
    local file done=" "
    for file in $NGINX_COMPOSE; do
        [ -f "$file" ] || continue
        case "$done" in *" $file "*) continue ;; esac
        done="$done$file "
        echo "$file"
    done
}
# "<folder> <commit>" for each site whose folder is a git checkout
site_commits() {
    local file dir
    for file in $(site_files); do
        dir=$(dirname "$file")
        git -C "$dir" rev-parse HEAD > /dev/null 2>&1 && echo "$dir $(git -C "$dir" rev-parse HEAD)"
    done
}
# build the sites' images on the NGINX_IMAGE in versions.env (nothing to build for a site whose nginx is
# the plain image, such as HyRoute), before production is touched
site_build() {
    local file
    for file in $(site_files); do
        log "Building the site in $(dirname "$file") on the tested nginx image"
        nginx_compose "$file" build --pull nginx || return 1
    done
}
# recreate every site's nginx with the tested or built image, and check that each one runs and answers
site_up() {
    local file dir url
    for file in $(site_files); do
        dir=$(dirname "$file")
        log "Recreating the nginx of $dir"
        nginx_compose "$file" up --detach nginx || { echo "up $dir failed" >> "$RUN_DIR/sites.txt"; return 1; }
        sleep 3
        [ "$(nginx_compose "$file" ps --status running --services nginx 2> /dev/null)" = nginx ] \
            || { log "The nginx of $dir is not running"; echo "up $dir not running" >> "$RUN_DIR/sites.txt"; return 1; }
        echo "up $dir ok" >> "$RUN_DIR/sites.txt"
    done
    for url in $NGINX_CHECK_URLS; do
        if curl --silent --show-error --fail --output /dev/null --retry 5 --retry-delay 3 --retry-all-errors \
                --max-time 30 "$url"; then
            echo "check $url ok" >> "$RUN_DIR/sites.txt"
        else
            log "$url does not answer"; echo "check $url failed" >> "$RUN_DIR/sites.txt"; return 1
        fi
    done
}
# put each site's checkout back to the commit deployed before (.update/deployed_sites), when a push moved
# it and the checkout is clean; a hand-edited checkout is left alone, with a warning
site_rollback() {
    local dir commit deployed
    while read -r dir commit; do
        deployed=$(grep "^$dir " .update/deployed_sites 2> /dev/null | cut -d' ' -f2)
        [ -n "$deployed" ] && [ "$deployed" != "$commit" ] || continue
        if [ -n "$(git -C "$dir" status --porcelain)" ]; then
            log "WARNING: $dir has uncommitted changes; not put back to ${deployed:0:8}"
            continue
        fi
        log "Putting $dir back to the commit deployed before, ${deployed:0:8}"
        git -C "$dir" reset --hard --quiet "$deployed" && echo "reset $dir ${deployed:0:8}" >> "$RUN_DIR/sites.txt"
    done <<< "$(site_commits)"
}

# scripts/deployments.py inside the backend image, with the hysite_ops credentials
ops() {
    docker run --rm --network "$OPS_NETWORK" --user "$(id -u):$(id -g)" \
        --env OPS_CONNECTION_STRING --env OPS_MONGO_HOST --env OPS_MONGO_PORT --env OPS_USERNAME \
        --env OPS_PASSWORD --env OPS_AUTH_SOURCE --env OPS_CLIENT_TLS \
        --volume "$REPO:/repo" --workdir /repo --entrypoint python "$OPS_IMAGE" \
        scripts/deployments.py "$@"
}
record() {
    log "Status: $1 - $2"
    echo "$(date -u +%H:%M:%S) $1 $2" >> "$RUN_DIR/events.txt"
    ops record "$RUN_DIR" --status "$1" --message "$2" \
        || { log "WARNING: could not record to hysite_ops.deployments"; RECORD_FAILED=true; }
}
# the report email, after every run, to HYSITE_REPORT_EMAIL (nothing without it); a problem with it is only logged
send_report() {
    [ -n "${HYSITE_REPORT_EMAIL:-}" ] || return 0
    if python3 scripts/send_report.py "$RUN_DIR"; then
        log "Report emailed to $HYSITE_REPORT_EMAIL"
    else
        log "WARNING: the report email was not sent"
    fi
}
finish() {
    send_report
    # keep the newest run folders; the database keeps every run
    ls -1d .update/runs/*/ | head -n "-$KEEP_RUNS" | xargs --no-run-if-empty rm -rf
    if [ "$1" -eq 0 ] && [ "$RECORD_FAILED" = true ]; then
        log "Finished, but the run was not fully recorded in the database"
        exit 1
    fi
    exit "$1"
}

# the pinned files before this run, so a failed test or deploy can put them back
backup_pins() {
    rm -rf .update/backup && mkdir -p .update/backup
    for file in "${PINNED_FILES[@]}"; do
        [ -f "$file" ] && install -D --mode 644 "$file" ".update/backup/$file"
    done
}
restore_pins() {
    for file in "${PINNED_FILES[@]}"; do
        if [ -f ".update/backup/$file" ]; then cp ".update/backup/$file" "$file"; else rm -f "$file"; fi
    done
}
# true if the versions are the same as before this run (ignores the comment lines)
pins_unchanged() {
    for file in "${PINNED_FILES[@]}"; do
        [ -f ".update/backup/$file" ] || return 1
        diff -q <(grep -v '^#' "$file") <(grep -v '^#' ".update/backup/$file") > /dev/null || return 1
    done
}
save_run_files() {
    mkdir -p "$RUN_DIR/pinned"
    for file in "${PINNED_FILES[@]}"; do
        [ -f "$file" ] && install -D --mode 644 "$file" "$RUN_DIR/pinned/$file"
    done
}
# the MONGO_VERSION the MongoDB image was built with, e.g. 8.2.12; $1 = image or container
mongo_version() {
    docker "$1" inspect "$2" --format '{{range .Config.Env}}{{println .}}{{end}}' 2> /dev/null \
        | sed -n 's/^MONGO_VERSION=//p'
}
# true unless the new MongoDB image is a different release line (major.minor) from the running one
mongo_line_unchanged() {
    local running new
    running=$(mongo_version container mongoDB)
    [ -n "$running" ] || return 0  # no MongoDB container on this server (database elsewhere)
    new=$(grep -oE '^MONGO_IMAGE=.*' versions.env | cut -d= -f2-)
    [ -n "$new" ] || return 0
    docker pull --quiet "$new" > /dev/null 2>&1
    new=$(mongo_version image "$new")
    RUNNING_MONGO_LINE=${running%.*}
    NEW_MONGO_LINE=${new%.*}
    [ -z "$new" ] || [ "$RUNNING_MONGO_LINE" = "$NEW_MONGO_LINE" ]
}
installed_versions() {  # $1 = image name prefix, e.g. hysite-test
    for service in django-api web-to-py; do
        docker run --rm --entrypoint sh "$1-$service" -c 'python --version; pip freeze' \
            > "$RUN_DIR/installed-$service.txt" 2> /dev/null
    done
}

log "HySite update run $RUN_ID"
backup_pins
DEPLOYED_COMMIT=$(cat .update/deployed_commit 2> /dev/null || echo none)
DEPLOYED_SITES=$(cat .update/deployed_sites 2> /dev/null)

# 1. code
if [ "$GIT_UPDATE" = true ]; then
    log "Updating the code from origin/$BRANCH"
    if ! { git fetch --quiet origin "$BRANCH" && git merge --ff-only --quiet "origin/$BRANCH" \
           && git submodule update --init --recursive --quiet; }; then
        echo '{"run_id": "'"$RUN_ID"'", "started": "'"$(date -u --iso-8601=seconds)"'"}' > "$RUN_DIR/run.json"
        record git_failed "Could not fast-forward to origin/$BRANCH; check the server checkout for local changes"
        finish 1
    fi
fi
COMMIT=$(git rev-parse HEAD)
# the other sites' checkouts: "site <folder> <commit> new|same <subject>" (new: not the commit deployed before)
SITES=$(site_commits)
while read -r dir commit; do
    [ -n "$dir" ] || continue
    state=same
    grep -q "^$dir $commit\$" <<< "$DEPLOYED_SITES" || state=new
    echo "site $dir $commit $state $(git -C "$dir" log -1 --format=%s)" >> "$RUN_DIR/sites.txt"
done <<< "$SITES"
python3 - "$RUN_DIR/run.json" "$RUN_ID" "$(git rev-parse --abbrev-ref HEAD)" "$COMMIT" "$(git log -1 --format=%s)" "$(hostname)" <<'EOF'
import json, sys
from datetime import datetime, timezone
from pathlib import Path
path, run_id, branch, commit, subject, host = sys.argv[1:]
sites = {}
for line in Path(path).with_name("sites.txt").read_text().splitlines() if Path(path).with_name("sites.txt").exists() else []:
    kind, folder, site_commit, state, *subject_words = line.split(" ")
    if kind == "site":
        sites[folder.replace(".", "_")] = {"commit": site_commit, "new": state == "new", "subject": " ".join(subject_words)}
json.dump({"run_id": run_id, "started": datetime.now(timezone.utc).isoformat(), "host": host,
           "git": {"branch": branch, "commit": commit, "subject": subject}, "sites": sites}, open(path, "w"))
EOF
record running "Started at commit ${COMMIT:0:8}"

# 2. newest versions
log "Resolving the newest versions"
if ! python3 scripts/refresh_versions.py; then
    restore_pins
    record refresh_failed "scripts/refresh_versions.py failed"
    finish 1
fi
save_run_files

# 3. anything new?
if [ "$COMMIT" = "$DEPLOYED_COMMIT" ] && [ "$SITES" = "$DEPLOYED_SITES" ] && pins_unchanged; then
    restore_pins  # same versions; keep the old files so their timestamps stay meaningful
    # the frontend cleans old session files when it starts; on a week without a deploy, do it here
    prod_compose exec -T web-to-py python web2py.py -S hypatia -R scripts/sessions2trash.py -A -o -x 604800 \
        > /dev/null 2>&1 || log "WARNING: old session files were not cleaned up"
    record unchanged "No new code, versions or site checkouts since the last deploy"
    finish 0
fi

# 4. test against the sample database
log "Testing the new versions against the sample database"
test_compose down --volumes --remove-orphans > /dev/null 2>&1
if test_compose build --pull && site_build && test_compose up --detach \
        && python3 scripts/smoke_test.py "$TEST_URL" --wait "$SMOKE_WAIT" | tee "$RUN_DIR/smoke-test.txt"; then
    TEST_PASSED=true
else
    TEST_PASSED=false
    test_compose logs --no-color > "$RUN_DIR/test-logs.txt" 2>&1
fi
installed_versions hysite-test
test_compose down --volumes --remove-orphans > /dev/null 2>&1
if [ "$TEST_PASSED" = false ]; then
    restore_pins
    record test_failed "Tests or a site's build failed; production was not changed. Logs: $REPO/$RUN_DIR"
    finish 1
fi
record tested "All smoke tests passed on the sample database"

# 5. deploy
# MongoDB's release line (major.minor) is never changed by this job: the data files must be converted one
# release at a time, by hand, with backups (wiki: "MongoDB Upgrade Plan"). The tests above can't detect
# the problem, since they start from a fresh sample database. Patch updates within the line are fine.
if ! mongo_line_unchanged; then
    restore_pins
    record mongo_version_blocked "compose.yaml follows MongoDB $NEW_MONGO_LINE but production runs $RUNNING_MONGO_LINE; not deployed. A new MongoDB release line needs the manual upgrade procedure (wiki: MongoDB Upgrade Plan)"
    finish 1
fi
log "Deploying to production"
for image in "${BUILT_IMAGES[@]}"; do
    docker image inspect "$image:latest" > /dev/null 2>&1 && docker tag "$image:latest" "$image:previous"
done
if prod_compose build --pull && prod_compose up --detach --remove-orphans && site_up \
        && python3 scripts/smoke_test.py "$PROD_URL" --wait "$SMOKE_WAIT" | tee "$RUN_DIR/smoke-production.txt"; then
    git rev-parse HEAD > .update/deployed_commit
    site_commits > .update/deployed_sites
    installed_versions hysite
    record deployed "Deployed commit ${COMMIT:0:8} and passed the production smoke test"
    docker image prune --force > /dev/null
    docker builder prune --force --filter until=168h > /dev/null
    finish 0
fi

# production failed: go back to the previous images, versions and site checkouts
log "Production check failed; rolling back"
prod_compose logs --no-color > "$RUN_DIR/production-logs.txt" 2>&1
restore_pins
for image in "${BUILT_IMAGES[@]}"; do
    docker image inspect "$image:previous" > /dev/null 2>&1 && docker tag "$image:previous" "$image:latest"
done
site_rollback
if prod_compose up --detach --no-build --remove-orphans && site_build && site_up \
        && python3 scripts/smoke_test.py "$PROD_URL" --wait "$SMOKE_WAIT" | tee "$RUN_DIR/smoke-rollback.txt"; then
    record rolled_back "Production check failed; rolled back to the previous versions, which pass. Logs: $REPO/$RUN_DIR"
else
    record rollback_failed "Production check failed and the rollback also fails. The website needs attention now. Logs: $REPO/$RUN_DIR"
fi
finish 1
