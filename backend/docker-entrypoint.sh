#!/bin/sh
# Container start-up for the django-api service.
#
# Work that needs MongoDB happens here, when the container starts, so the
# image build never needs database credentials or host networking.
set -e

if [ "$1" = "gunicorn" ]; then
    # Redraw the homepage histogram from the database. If the database can't be
    # reached in time, start the API anyway with the last plot saved in the
    # website_plots volume.
    timeout 120 python update.py --make-website-plots \
        || echo "WARNING: website plots were not refreshed" >&2
    # Put the static files and the plots in the volume nginx serves. Once, here,
    # rather than in every gunicorn worker (see copy_static.py).
    python copy_static.py
fi

exec "$@"
