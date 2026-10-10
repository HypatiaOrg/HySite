#!/bin/bash
# Build a complete, fresh MongoDB data directory from a dump, with a chosen MongoDB image.
#
#   scripts/restore_mongo.sh <dump-name> [--image mongo:9.0] [--data-dir mongo/data-new | --volume NAME]
#
# This is how to move to a new MongoDB release line when the in-place upgrade is not possible or not
# wanted (wiki page "MongoDB Upgrade Plan"): no intermediate versions, no feature compatibility steps,
# and the old data directory stays untouched for a rollback.
#
#  1. Starts a temporary MongoDB container from the image (default: the line compose.yaml follows, or
#     BACKUP_IMAGE / MONGO_IMAGE) on an empty data directory (default mongo/data-<image tag>), with no
#     authentication and no published port. --volume NAME uses a new Docker volume instead of a
#     directory, for machines where the repository is not on a filesystem MongoDB can use (a sandbox
#     with the repository on a shared mount); the server uses a directory, like mongo/data.
#  2. mongorestore the dump from mongo/backups/<dump-name>: public, metadata, and admin if the dump
#     was made with "backup_mongo.sh --users" (every user, role and IP restriction). Without admin
#     the new database has NO users: make the dump with --users.
#  3. Prints the version, feature compatibility version, document counts and users, stops and removes
#     the container, and prints the cut-over commands. Nothing running is changed.
#
# Needs Docker and .env (MONGO_GLIBC_TUNABLES is passed to the container, as compose.yaml does).
set -euo pipefail

REPO=$(cd "$(dirname "$0")/.." && pwd)
cd "$REPO"
BACKUP_DIR=${BACKUP_DIR:-mongo/backups}
CONTAINER=hysite-restore

name=""
image=""
data_dir=""
volume=""
while [ $# -gt 0 ]; do
    case "$1" in
        --image) image=$2; shift ;;
        --data-dir) data_dir=$2; shift ;;
        --volume) volume=$2; shift ;;
        -h | --help) sed -n '2,19p' "$0" | cut -c3-; exit 0 ;;
        -*) echo "unknown option: $1"; exit 1 ;;
        *) name=$1 ;;
    esac
    shift
done
[ -n "$name" ] || { echo "usage: scripts/restore_mongo.sh <dump-name> [--image IMAGE] [--data-dir DIR]"; exit 1; }
dump_dir=$BACKUP_DIR/$name
[ -d "$dump_dir/public" ] || { echo "no dump at $dump_dir (public/ missing); run scripts/backup_mongo.sh $name --users first"; exit 1; }
if [ ! -d "$dump_dir/admin" ]; then
    echo "WARNING: $dump_dir has no admin database, so the new database will have no users."
    echo "         Make the dump with: scripts/backup_mongo.sh $name --dump-only --users"
fi

# the same .env reader as backup_mongo.sh: compose rules, nothing run as shell
load_env_file() {
    local line key value
    while IFS= read -r line || [ -n "$line" ]; do
        line=${line%$'\r'}
        case $line in ''|'#'*) continue ;; esac
        [[ $line == *=* ]] || continue
        key=${line%%=*}
        key=${key#export }
        key=${key//[[:space:]]/}
        [[ $key =~ ^[A-Za-z_][A-Za-z0-9_]*$ ]] || continue
        value=${line#*=}
        if [[ $value == \"*\" || $value == \'*\' ]] && [ ${#value} -ge 2 ]; then
            value=${value:1:${#value}-2}
        fi
        export "$key=$value"
    done < "$1"
}
[ -f .env ] && load_env_file .env
IMAGE=${image:-${BACKUP_IMAGE:-${MONGO_IMAGE:-$(sed -n 's/.*\${MONGO_IMAGE:-\([^}]*\)}.*/\1/p' compose.yaml)}}}
if [ -n "$volume" ]; then
    docker volume inspect "$volume" > /dev/null 2>&1 && { echo "volume $volume already exists; choose another --volume or remove it: docker volume rm $volume"; exit 1; }
    docker volume create "$volume" > /dev/null
    mount="$volume:/data/db"
    where="volume $volume"
else
    data_dir=${data_dir:-mongo/data-${IMAGE##*:}}
    data_dir=${data_dir%/}
    if [ -e "$data_dir" ] && [ -n "$(ls -A "$data_dir")" ]; then
        echo "$data_dir exists and is not empty; choose another --data-dir or remove it"; exit 1
    fi
    mkdir -p "$data_dir"
    mount="$REPO/$data_dir:/data/db"
    where="$data_dir"
fi
docker container inspect "$CONTAINER" > /dev/null 2>&1 && { echo "$CONTAINER already exists; remove it: docker rm -f $CONTAINER"; exit 1; }

tool() {  # tool <name> <docker run options...> -- <tool arguments...>
    local name=$1; shift
    local options=()
    while [ "$1" != "--" ]; do options+=("$1"); shift; done; shift
    docker run --rm --user "$(id -u):$(id -g)" --entrypoint "$name" "${options[@]}" "$IMAGE" "$@"
}
cleanup() { docker rm -f "$CONTAINER" > /dev/null 2>&1 || true; }
trap cleanup EXIT

# 1. a temporary MongoDB with no users yet, so the restore needs no credentials
echo "Starting $IMAGE on $where (container $CONTAINER, no authentication, not published)"
docker run --detach --name "$CONTAINER" --volume "$mount" \
    --env "GLIBC_TUNABLES=${MONGO_GLIBC_TUNABLES:-glibc.pthread.rseq=0}" "$IMAGE" > /dev/null
echo -n "Waiting for $CONTAINER"
ready=false
for _ in $(seq 60); do
    if docker exec "$CONTAINER" mongosh --quiet --eval 'db.adminCommand("ping").ok' > /dev/null 2>&1; then ready=true; break; fi
    if [ "$(docker inspect "$CONTAINER" --format '{{.State.Running}}')" != true ]; then break; fi
    echo -n "."; sleep 2
done
echo
if [ "$ready" != true ]; then
    echo "$IMAGE did not start. Its log:"
    docker logs "$CONTAINER" 2>&1 | grep -oE '"msg":"[^"]*"' | tail -5
    echo "Remove $where before trying again."
    exit 1
fi

# 2. restore the data, one database at a time
restore() {  # restore <mongorestore arguments...>
    tool mongorestore --network "container:$CONTAINER" --volume "$REPO/$dump_dir:/dump:ro" -- \
        --host localhost --drop "$@" 2>&1 | grep -E "document\(s\) restored|Failed|error" | sed 's/^/  /'
    return "${PIPESTATUS[0]}"
}
echo "Restoring $dump_dir"
for database in public metadata; do
    [ -d "$dump_dir/$database" ] || continue
    echo "  $database:"
    restore --db "$database" "/dump/$database"
done
# Users and roles. mongorestore's own path for them fails with dumps of MongoDB 8.x and newer (it
# looks for an "authSchema" document that these versions no longer keep), so this does what
# mongorestore does internally: load the dump's user and role documents into temporary collections,
# then let the server merge them with _mergeAuthzCollections (the command the tools use).
if [ -f "$dump_dir/admin/system.users.bson" ]; then
    echo "  users and roles:"
    restore --db admin --collection tempusers /dump/admin/system.users.bson
    if [ -f "$dump_dir/admin/system.roles.bson" ]; then
        restore --db admin --collection temproles /dump/admin/system.roles.bson
    fi
    docker exec "$CONTAINER" mongosh --quiet --eval '
        const admin = db.getSiblingDB("admin");
        if (!admin.getCollectionNames().includes("temproles")) admin.createCollection("temproles");
        const result = admin.runCommand({_mergeAuthzCollections: 1, tempUsersCollection: "admin.tempusers",
                                         tempRolesCollection: "admin.temproles", drop: true, db: ""});
        admin.tempusers.drop(); admin.temproles.drop();
        if (result.ok !== 1) { print("  merging users failed: " + JSON.stringify(result)); quit(1); }'
fi

# 3. what the new database holds
echo "The new database holds:"
docker exec "$CONTAINER" mongosh --quiet --eval '
    print("  MongoDB " + db.version() + ", feature compatibility version " + db.adminCommand({getParameter: 1, featureCompatibilityVersion: 1}).featureCompatibilityVersion.version
          + ", allocator per-CPU caches: " + db.serverStatus().tcmalloc.usingPerCPUCaches);
    for (const name of ["public", "metadata"]) {
        const database = db.getSiblingDB(name);
        for (const collection of database.getCollectionNames().sort())
            print("  " + name + "." + collection + ": " + database.getCollection(collection).countDocuments() + " documents");
    }
    const admin = db.getSiblingDB("admin");
    const names = admin.getUsers().users.map(u => u.user);
    print("  users: " + names.length);
    for (const name of names) {
        const user = admin.getUser(name, {showAuthenticationRestrictions: true});
        const roles = user.roles.map(r => r.role + "@" + r.db).join(", ");
        const restrictions = (user.authenticationRestrictions || []).map(r => (r.clientSource || []).join("|")).filter(Boolean).join("; ");
        print("    " + user.user + ": " + roles + (restrictions ? "  [from " + restrictions + "]" : ""));
    }'
docker stop "$CONTAINER" > /dev/null
cleanup
trap - EXIT

old_dir="mongo/data-old-$(date -u +%Y-%m-%dT%H-%M-%SZ)"
echo
echo "Done: $where is a complete $IMAGE database. Nothing running was changed."
if [ -n "$volume" ]; then
    echo "To use it as a directory (what compose.yaml mounts):"
    echo "  docker run --rm --volume $volume:/from --volume \"\$PWD/mongo/data-new:/to\" alpine cp -a /from/. /to/"
    echo "then continue with mongo/data-new as below."
    data_dir=mongo/data-new
fi
echo "To put it into production (a few seconds of downtime; the old directory is the rollback):"
echo "  docker compose stop mongo-db"
echo "  mv mongo/data $old_dir && mv $data_dir mongo/data"
echo "  MONGO_IMAGE=$IMAGE docker compose up -d mongo-db     # then set the default in compose.yaml"
echo "Rollback: docker compose stop mongo-db && mv mongo/data $data_dir && mv $old_dir mongo/data && docker compose up -d mongo-db"
