# Use an official Python runtime as a parent image
FROM python:alpine
ENV PYTHONUNBUFFERED 1
ARG WORKING_DIR=/home/mz_python/django_app
ARG DATA_OUTPUT_DIR=$WORKING_DIR/output
ARG STATIC_ROOT_DIR=$WORKING_DIR/static_root
ARG VENV_DIR=$WORKING_DIR/venv
ARG MPLCONFIGDIR=$WORKING_DIR/.config/matplotlib
# Set the working directory
WORKDIR $WORKING_DIR
ENV PYTHONPATH "${PYTHONPATH}:${WORKING_DIR}"
# setup a username and group
RUN addgroup --system --gid 1001 monty_group
RUN adduser --system --uid 1001 mz_python --ingroup monty_group
# initalize a directory for static files
RUN mkdir -p $STATIC_ROOT_DIR
RUN chown mz_python:monty_group $STATIC_ROOT_DIR
# initalize a directory downloadable files
RUN mkdir -p $DATA_OUTPUT_DIR
RUN chown mz_python:monty_group $DATA_OUTPUT_DIR
# add a cache directory for matplotlib
RUN mkdir -p $MPLCONFIGDIR
RUN chown mz_python:monty_group $MPLCONFIGDIR
# install the required packages
RUN apk update && apk add --no-cache build-base
# update pip
RUN pip install --upgrade pip
# create a virtual environment
RUN python -m venv $VENV_DIR
# activate the virtual environment
RUN source $VENV_DIR/bin/activate
# install the required packages
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
# Copy the current directory contents into the container
COPY . .
# switch to the python user
USER mz_python
# collect the static files
RUN python manage.py collectstatic --clear --noinput
