# Use an official Python runtime as a parent image
# The Python image is set in compose.yaml (BASE_IMAGE), next to the other image versions
ARG BASE_IMAGE
FROM ${BASE_IMAGE}
ENV PYTHONUNBUFFERED=1
ARG WORKING_DIR=/home/mz_python/django_app
ARG DATA_OUTPUT_DIR=$WORKING_DIR/output
ARG WEBSITE_PLOTS_DIR=$DATA_OUTPUT_DIR/website
ARG STATIC_FILES_DIR=/app/static
ARG STATIC_ROOT_DIR=$WORKING_DIR/static_root
# /var/tmp is a writable volume in compose.yaml, which matters when READ_ONLY=true
ARG MPLCONFIGDIR=/var/tmp/matplotlib
ENV MPLCONFIGDIR=$MPLCONFIGDIR
# MongoDB settings are provided at runtime by compose.yaml, never at build time
# Set the working directory
WORKDIR $WORKING_DIR
ENV PYTHONPATH "${PYTHONPATH}:${WORKING_DIR}"
# setup a username and group
RUN addgroup --system --gid 1001 monty_group
RUN adduser --system --uid 1001 mz_python --ingroup monty_group
# initalize a directory for static files
RUN mkdir -p $STATIC_ROOT_DIR
RUN chown mz_python:monty_group $STATIC_ROOT_DIR
# initialize a volume directory for static files
RUN mkdir -p $STATIC_FILES_DIR
RUN chown mz_python:monty_group $STATIC_FILES_DIR
# add a cache directory for matplotlib
RUN mkdir -p $MPLCONFIGDIR
RUN chown mz_python:monty_group $MPLCONFIGDIR
# install the required packages
RUN apk update && apk add --no-cache build-base
# update pip
RUN pip install --upgrade pip
# install the required packages
# requirements.txt lists the packages, unpinned. The server's update job builds from
# requirements.lock, the exact tested versions, with --build-arg REQUIREMENTS=requirements.lock
ARG REQUIREMENTS=requirements.txt
# the * also copies requirements.lock when it exists
COPY requirements.* ./
RUN pip install --no-cache-dir -r $REQUIREMENTS
# Copy the current directory contents into the container
COPY . .
# let this user own the website plots directory
RUN mkdir -p $WEBSITE_PLOTS_DIR
RUN chown -R mz_python:monty_group $WEBSITE_PLOTS_DIR
# switch to the python user
USER mz_python
# collect the static files (no database needed)
RUN python manage.py collectstatic --clear --noinput
# database work, like making the homepage plot, runs when the container starts
ENTRYPOINT ["/bin/sh", "docker-entrypoint.sh"]
