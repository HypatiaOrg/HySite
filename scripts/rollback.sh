#!/bin/bash
# Roll production back.
#   scripts/rollback.sh            the images and versions from before the last deploy
#   scripts/rollback.sh <run id>   rebuild the versions recorded for an earlier run;
#                                  see the run ids with: scripts/rollback.sh --list
# Uses the same settings as the update job, from /etc/hysite/update.env (read with sudo).
set -uo pipefail
cd "${HYSITE_REPO:-/home/ubuntu/HySite}" || exit 1
prod_compose() { COMPOSE_ENV_FILES=.env,versions.env docker compose "$@"; }
ops() {
    sudo cat /etc/hysite/update.env | docker run --rm --interactive --network "${OPS_NETWORK:-hynet}" \
        --user "$(id -u):$(id -g)" --volume "$PWD:/repo" --workdir /repo --entrypoint sh \
        hysite-django-api:latest -c 'set -a; . /dev/stdin; set +a; python scripts/deployments.py "$@"' sh "$@"
}

case "${1:-}" in
    --list)
        ops list --limit 20 ;;
    "")
        for file in versions.env backend/requirements.lock frontend-web2py/requirements.lock; do
            if [ -f ".update/backup/$file" ]; then cp ".update/backup/$file" "$file"; else rm -f "$file"; fi
        done
        for image in hysite-django-api hysite-web-to-py; do
            docker image inspect "$image:previous" > /dev/null 2>&1 \
                || { echo "No $image:previous image to roll back to; try: scripts/rollback.sh --list"; exit 1; }
            docker tag "$image:previous" "$image:latest"
        done
        prod_compose up --detach --no-build --remove-orphans || exit
        echo "Rolled back to the images and versions from before the last deploy." ;;
    *)
        ops restore "$1" || exit
        prod_compose build --pull && prod_compose up --detach --remove-orphans || exit
        echo "Rebuilt production with the versions recorded for run $1." ;;
esac
echo "The git checkout is unchanged (run: git log --oneline -5). The next weekly update moves to the newest versions again."
