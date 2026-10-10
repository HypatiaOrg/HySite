# The Python image is set in compose.yaml (BASE_IMAGE), next to the other image versions
ARG BASE_IMAGE
FROM ${BASE_IMAGE}
ENV PYTHONUNBUFFERED=1
ARG WORKING_DIR=/home/python_kid/web2py_app
ARG TEMP_DIR=$WORKING_DIR/temp_data
ARG SESSION_DIR=$WORKING_DIR/applications/hypatia/sessions
# set the directroy to install all the files
WORKDIR $WORKING_DIR
# setup a username and group
RUN addgroup --system --gid 1001 python_kia
RUN adduser --system --uid 1001 python_kid --ingroup python_kia
# update pip
RUN pip install --upgrade pip
# requirements.txt lists the packages, unpinned. The server's update job builds from
# requirements.lock, the exact tested versions, with --build-arg REQUIREMENTS=requirements.lock
ARG REQUIREMENTS=requirements.txt
# the * also copies requirements.lock when it exists
COPY requirements.* ./
# install the python requirments
RUN pip install --no-cache-dir -r $REQUIREMENTS
# web2py's soft cron (on by default in anyserver.py) keeps its lock in cron.master, which must be
# writable: it lives in the temp_data volume, linked from where web2py looks for it
RUN mkdir -p $TEMP_DIR
RUN touch $TEMP_DIR/cron.master
RUN chown python_kid:python_kia $TEMP_DIR/cron.master
RUN ln -s $TEMP_DIR/cron.master $WORKING_DIR/cron.master
# the folders web2py expects and would otherwise try to create on every request (gluon/fileutils.py:
# create_missing_folders and missing_app_folders), which a read-only container cannot do
RUN mkdir -p $WORKING_DIR/deposit $WORKING_DIR/site-packages $WORKING_DIR/logs
RUN mkdir -p $SESSION_DIR
RUN chown python_kid:python_kia $SESSION_DIR
# the rest of the files
COPY ./web2py .
COPY ./app ./applications/hypatia
RUN mkdir -p applications/hypatia/databases applications/hypatia/private applications/hypatia/uploads \
    applications/hypatia/cron applications/hypatia/errors
COPY ./configs ./.
COPY docker-entrypoint.sh ./
# switch to the python user
USER python_kid
# housekeeping at start (old session files), then the server command from compose.yaml
ENTRYPOINT ["/bin/sh", "docker-entrypoint.sh"]
