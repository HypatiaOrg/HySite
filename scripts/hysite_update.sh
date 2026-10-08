#!/bin/bash
# HySite update job: newest versions -> test -> deploy -> record.
#
# Run weekly on the production server by deploy/systemd/hysite-update.timer, or now with
# scripts/update.sh. Settings come from /etc/hysite/update.env (deploy/systemd/update.env.example).
#
#  1. Update the code: fast-forward to origin/$HYSITE_BRANCH.
#  2. Resolve the newest versions: scripts/refresh_versions.py writes versions.env and the
#     requirements.lock files (ignored by git).
#  3. Stop here if neither the code nor any version changed.
#  4. Test: build and run the whole site against the sample database (compose.test.yaml)
#     and run the smoke tests. On failure: put the previous versions back, stop.
#  5. Deploy: rebuild production from the tested versions and recreate changed containers,
#     keeping the old images as :previous. Smoke test production. On failure: roll back.
#  6. Every step is recorded in the hysite_ops.deployments collection (scripts/deployments.py).
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
    ops record "$RUN_DIR" --status "$1" --message "$2" \
        || { log "WARNING: could not record to hysite_ops.deployments"; RECORD_FAILED=true; }
}
finish() {
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
installed_versions() {  # $1 = image name prefix, e.g. hysite-test
    for service in django-api web-to-py; do
        docker run --rm --entrypoint sh "$1-$service" -c 'python --version; pip freeze' \
            > "$RUN_DIR/installed-$service.txt" 2> /dev/null
    done
}

log "HySite update run $RUN_ID"
backup_pins
DEPLOYED_COMMIT=$(cat .update/deployed_commit 2> /dev/null || echo none)

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
python3 - "$RUN_DIR/run.json" "$RUN_ID" "$(git rev-parse --abbrev-ref HEAD)" "$COMMIT" "$(git log -1 --format=%s)" "$(hostname)" <<'EOF'
import json, sys
from datetime import datetime, timezone
path, run_id, branch, commit, subject, host = sys.argv[1:]
json.dump({"run_id": run_id, "started": datetime.now(timezone.utc).isoformat(), "host": host,
           "git": {"branch": branch, "commit": commit, "subject": subject}}, open(path, "w"))
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
if [ "$COMMIT" = "$DEPLOYED_COMMIT" ] && pins_unchanged; then
    restore_pins  # same versions; keep the old files so their timestamps stay meaningful
    record unchanged "No new code or versions since the last deploy"
    finish 0
fi

# 4. test against the sample database
log "Testing the new versions against the sample database"
test_compose down --volumes --remove-orphans > /dev/null 2>&1
if test_compose build --pull && test_compose up --detach \
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
    record test_failed "Tests failed; production was not changed. Logs: $REPO/$RUN_DIR"
    finish 1
fi
record tested "All smoke tests passed on the sample database"

# 5. deploy
log "Deploying to production"
for image in "${BUILT_IMAGES[@]}"; do
    docker image inspect "$image:latest" > /dev/null 2>&1 && docker tag "$image:latest" "$image:previous"
done
if prod_compose build --pull && prod_compose up --detach --remove-orphans \
        && python3 scripts/smoke_test.py "$PROD_URL" --wait "$SMOKE_WAIT" | tee "$RUN_DIR/smoke-production.txt"; then
    git rev-parse HEAD > .update/deployed_commit
    installed_versions hysite
    record deployed "Deployed commit ${COMMIT:0:8} and passed the production smoke test"
    docker image prune --force > /dev/null
    docker builder prune --force --filter until=168h > /dev/null
    finish 0
fi

# production failed: go back to the previous images and versions
log "Production check failed; rolling back"
prod_compose logs --no-color > "$RUN_DIR/production-logs.txt" 2>&1
restore_pins
for image in "${BUILT_IMAGES[@]}"; do
    docker image inspect "$image:previous" > /dev/null 2>&1 && docker tag "$image:previous" "$image:latest"
done
if prod_compose up --detach --no-build --remove-orphans \
        && python3 scripts/smoke_test.py "$PROD_URL" --wait "$SMOKE_WAIT" | tee "$RUN_DIR/smoke-rollback.txt"; then
    record rolled_back "Production check failed; rolled back to the previous versions, which pass. Logs: $REPO/$RUN_DIR"
else
    record rollback_failed "Production check failed and the rollback also fails. The website needs attention now. Logs: $REPO/$RUN_DIR"
fi
finish 1
