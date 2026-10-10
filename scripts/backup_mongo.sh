#!/bin/bash
# Copy the HySite database into a local MongoDB container: a backup, and a place to rehearse upgrades.
#
#   scripts/backup_mongo.sh [name] [--dump-only] [--users]
#
#  1. mongodump the public and metadata databases from the database in .env (production, read-only
#     user, TLS) into mongo/backups/<name>/, where <name> defaults to the current UTC date and time.
#     --users also dumps the admin database (every user with its roles, password hashes and IP
#     restrictions), which needs root or userAdminAnyDatabase on the source; the dump is then enough
#     to build a complete new database with scripts/restore_mongo.sh.
#  2. Restore that dump into a local MongoDB container named hysite-backup, with its own Docker
#     volume (hysite-backup-data) and the MongoDB image from compose.yaml, so the data files are the
#     same version as production's. It listens on 127.0.0.1:${BACKUP_PORT:-27018} without TLS, as
#     user admin with the password in mongo/backups/backup.env (made on the first run).
#     A later run restores over the container's data (collections in the dump are dropped first).
#
# Reads only from the source database. Needs Docker and the settings in .env (MONGO_HOST,
# MONGO_USERNAME, MONGO_PASSWORD, CLIENT_TLS, or CONNECTION_STRING; another file with
# BACKUP_ENV_FILE=...). The dump folder stays on disk: keep it, or delete it once the container
# holds the copy. Dumps are ignored by git.
#
# To rehearse a MongoDB upgrade on the copy, see the wiki page "MongoDB Upgrade Plan".
set -euo pipefail

REPO=$(cd "$(dirname "$0")/.." && pwd)
cd "$REPO"
DATABASES=(public metadata)
BACKUP_DIR=${BACKUP_DIR:-mongo/backups}
BACKUP_PORT=${BACKUP_PORT:-27018}
CONTAINER=hysite-backup
VOLUME=hysite-backup-data

name=""
dump_only=false
for arg in "$@"; do
    case "$arg" in
        --dump-only) dump_only=true ;;
        --users) DATABASES+=(admin) ;;
        -h | --help) sed -n '2,18p' "$0" | cut -c3-; exit 0 ;;
        -*) echo "unknown option: $arg"; exit 1 ;;
        *) name=$arg ;;
    esac
done
name=${name:-$(date -u +%Y-%m-%dT%H-%M-%SZ)}

# Read a Docker Compose .env file the way compose does (KEY=value lines, optional matching quotes,
# comments), without running it as shell: a password with ( or $ in it must not break or run anything.
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
# the website's database settings
ENV_FILE=${BACKUP_ENV_FILE:-.env}
[ -f "$ENV_FILE" ] || { echo "$ENV_FILE not found in $REPO"; exit 1; }
load_env_file "$ENV_FILE"
# the image line compose.yaml follows, e.g. mongo:8.2 (MONGO_IMAGE from versions.env takes priority)
IMAGE=${MONGO_IMAGE:-$(sed -n 's/.*\${MONGO_IMAGE:-\([^}]*\)}.*/\1/p' compose.yaml)}
IMAGE=${BACKUP_IMAGE:-$IMAGE}

# mongodump and mongorestore come from the MongoDB image. The image's entrypoint switches every
# mongo* command to its own user, which can't write our folders, so the tools run directly.
tool() {  # tool <name> <docker run options...> -- <tool arguments...>
    local name=$1; shift
    local options=()
    while [ "$1" != "--" ]; do options+=("$1"); shift; done; shift
    docker run --rm --user "$(id -u):$(id -g)" --entrypoint "$name" "${options[@]}" "$IMAGE" "$@"
}

# 1. dump
dump_dir=$BACKUP_DIR/$name
mkdir -p "$dump_dir"
# the connection settings go in a file (mode 600) rather than on the command line; the tools'
# --config accepts only "uri" and "password", so the user name is part of the URI
config=$dump_dir/.source.yaml
umask 077
if [ -n "${CONNECTION_STRING:-}" ] && [ "${CONNECTION_STRING,,}" != none ]; then
    echo "uri: \"$CONNECTION_STRING\"" > "$config"
else
    case "${CLIENT_TLS:-true}" in true | True | TRUE | yes | 1) tls=true ;; *) tls=false ;; esac
    user=$(python3 -c 'import sys, urllib.parse; print(urllib.parse.quote(sys.argv[1], safe=""))' "${MONGO_USERNAME:-admin}")
    {
        echo "uri: \"mongodb://$user@${MONGO_HOST:-hypatiacatalog.com}:${MONGO_PORT:-27017}/?authSource=admin&tls=$tls\""
        echo "password: \"${MONGO_PASSWORD:-}\""
    } > "$config"
fi
umask 022
echo "Dumping ${DATABASES[*]} from ${MONGO_HOST:-hypatiacatalog.com} to $dump_dir (image $IMAGE)"
for database in "${DATABASES[@]}"; do
    tool mongodump --volume "$REPO/$dump_dir:/dump" -- --config /dump/.source.yaml --db "$database" --out /dump --quiet
    echo "  $database: $(find "$dump_dir/$database" -name '*.bson' | wc -l) collections, $(du -sh "$dump_dir/$database" | cut -f1)"
done
rm -f "$config"
if [ "$dump_only" = true ]; then
    echo "Dump finished: $dump_dir"
    exit 0
fi

# 2. restore into the local container
password_file=$BACKUP_DIR/backup.env
if [ ! -f "$password_file" ]; then
    umask 077
    echo "BACKUP_PASSWORD=$(head -c 36 /dev/urandom | base64 | tr -dc 'A-Za-z0-9' | head -c 40)" > "$password_file"
    umask 022
fi
# shellcheck disable=SC1090
. "$password_file"
if ! docker container inspect "$CONTAINER" > /dev/null 2>&1; then
    echo "Creating the $CONTAINER container ($IMAGE, volume $VOLUME, port 127.0.0.1:$BACKUP_PORT)"
    docker volume create "$VOLUME" > /dev/null
    docker run --detach --name "$CONTAINER" --restart unless-stopped \
        --publish "127.0.0.1:$BACKUP_PORT:27017" --volume "$VOLUME:/data/db" \
        --env MONGO_INITDB_ROOT_USERNAME=admin --env MONGO_INITDB_ROOT_PASSWORD="$BACKUP_PASSWORD" \
        --env "GLIBC_TUNABLES=${MONGO_GLIBC_TUNABLES:-glibc.pthread.rseq=0}" \
        "$IMAGE" > /dev/null
else
    docker start "$CONTAINER" > /dev/null
fi
# a new container first runs a temporary mongod without authentication to create the admin user, then
# restarts with authentication; a ping with the password only succeeds once that is done
echo -n "Waiting for $CONTAINER"
ready=false
for _ in $(seq 90); do
    if docker exec "$CONTAINER" mongosh --quiet --username admin --password "$BACKUP_PASSWORD" \
            --eval 'db.adminCommand("ping").ok' > /dev/null 2>&1; then ready=true; break; fi
    echo -n "."; sleep 2
done
echo
[ "$ready" = true ] || { echo "$CONTAINER did not start; see: docker logs $CONTAINER"; exit 1; }
umask 077
echo "password: \"$BACKUP_PASSWORD\"" > "$config"
umask 022
if [ -d "$dump_dir/admin" ]; then
    echo "The dump has the admin database: the copy's users will be the source's (BACKUP_PASSWORD no longer applies)"
fi
echo "Restoring into $CONTAINER"
tool mongorestore --network "container:$CONTAINER" --volume "$REPO/$dump_dir:/dump:ro" -- \
    --config /dump/.source.yaml --host localhost --username admin --authenticationDatabase admin \
    --drop --quiet /dump
rm -f "$config"

echo "The copy now holds:"
docker exec "$CONTAINER" mongosh --quiet --username admin --password "$BACKUP_PASSWORD" --eval '
    print("  MongoDB " + db.version() + ", feature compatibility version " + db.adminCommand({getParameter: 1, featureCompatibilityVersion: 1}).featureCompatibilityVersion.version);
    for (const name of ["public", "metadata"]) {
        const database = db.getSiblingDB(name);
        for (const collection of database.getCollectionNames().sort())
            print("  " + name + "." + collection + ": " + database.getCollection(collection).countDocuments() + " documents");
    }'
echo "Connect with: mongodb://admin:<BACKUP_PASSWORD from $password_file>@localhost:$BACKUP_PORT/?authSource=admin"
echo "Dump kept in $dump_dir"
