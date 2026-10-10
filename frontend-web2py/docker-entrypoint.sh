#!/bin/sh
# Container start-up for the web-to-py service: housekeeping, then the server.
set -e
# Session files (one per visitor) are never removed by web2py itself. Drop the ones no one has used
# for a week; a visitor whose session was dropped just gets the default settings again.
python web2py.py -S hypatia -R scripts/sessions2trash.py -A -o -x 604800 > /dev/null 2>&1 \
    || echo "WARNING: old session files were not cleaned up" >&2
exec "$@"
