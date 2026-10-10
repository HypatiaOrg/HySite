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
        --entrypoint python hysite-django-api:latest -c '
# read update.env from stdin the way compose and systemd do (KEY=value, optional quotes), not as shell
import os, sys
for line in sys.stdin:
    line = line.strip()
    if not line or line.startswith("#") or "=" not in line:
        continue
    key, value = (part.strip() for part in line.split("=", 1))
    key = key.removeprefix("export").strip()
    if not key.replace("_", "a").isalnum():
        continue
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"\x27":
        value = value[1:-1]
    os.environ[key] = value
os.execvp("python", ["python", "scripts/deployments.py", *sys.argv[1:]])' "$@"
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
