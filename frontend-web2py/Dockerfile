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
# # create the logs and writable files for the python user
RUN mkdir -p $TEMP_DIR
RUN touch $TEMP_DIR/cron.master
RUN chown python_kid:python_kia $TEMP_DIR/cron.master
RUN ln -s $TEMP_DIR/cron.master $WORKING_DIR/cron.master
RUN touch $TEMP_DIR/web2py.log
RUN chown python_kid:python_kia $TEMP_DIR/web2py.log
RUN ln -s $TEMP_DIR/web2py.log $WORKING_DIR/web2py.log
# create the session directory
RUN mkdir -p $SESSION_DIR
RUN chown python_kid:python_kia $SESSION_DIR
# the rest of the files
COPY ./web2py .
COPY ./app ./applications/hypatia
COPY ./configs ./.
# switch to the python user
USER python_kid
