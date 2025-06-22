# Use an official Python runtime as a parent image
FROM python:alpine
ENV PYTHONUNBUFFERED 1
ARG WORKING_DIR=/home/mz_python/django_app
ARG DATA_OUTPUT_DIR=$WORKING_DIR/output
ARG WEBSITE_PLOTS_DIR=$DATA_OUTPUT_DIR/website
ARG STATIC_FILES_DIR=/app/static
ARG STATIC_ROOT_DIR=$WORKING_DIR/static_root
ARG VENV_DIR=$WORKING_DIR/venv
ARG MPLCONFIGDIR=$WORKING_DIR/.config/matplotlib
# MongoDB configurations
ARG MONGO_USERNAME
ARG MONGO_PASSWORD
ARG MONGO_HOST
ARG MONGO_DATABASE
ARG MONGO_STARNAMES_COLLECTION
ENV MONGO_USERNAME=$MONGO_USERNAME
ENV MONGO_PASSWORD=$MONGO_PASSWORD
ENV MONGO_HOST=$MONGO_HOST
ENV MONGO_DATABASE=$MONGO_DATABASE
ENV MONGO_STARNAMES_COLLECTION=$MONGO_STARNAMES_COLLECTION
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
# create a virtual environment
RUN python -m venv $VENV_DIR
# activate the virtual environment
RUN source $VENV_DIR/bin/activate
# install the required packages
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
# Copy the current directory contents into the container
COPY . .
# let this user own the website plots directory
RUN mkdir -p $WEBSITE_PLOTS_DIR
RUN chown mz_python:monty_group $WEBSITE_PLOTS_DIR
# switch to the python user
USER mz_python
# create the website plots
RUN python update.py --make-website-plots
# collect the static files
RUN python manage.py collectstatic --clear --noinput
