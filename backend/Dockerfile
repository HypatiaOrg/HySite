# Use an official Python runtime as a parent image
FROM python:3
ENV PYTHONUNBUFFERED 1
# Set the working directory to /app
WORKDIR /app
ENV PYTHONPATH "${PYTHONPATH}:/app"
# update the package list
RUN apt-get update -y
# update pip
RUN pip install --upgrade pip
# setup a username and group
RUN addgroup --system --gid 1001 python_group
RUN adduser --system --uid 1001 python_user
# initalize a directory for static files
RUN mkdir /app/static_root
RUN chown python_user:python_group /app/static_root
# initalize a directory for the virtual environment
RUN mkdir /opt/venv
RUN chown python_user:python_group /opt/venv
# set the user
USER python_user
# create a virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
# install the required packages
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
# Copy the current directory contents into the container at /app
COPY --chown=python_user:python_group . .
## migrate the Django database and tables (The SQLite database is only a defualt initaliztion that is not used for a production database)
#RUN python manage.py makemigrations api
#RUN python manage.py migrate
# collect the static files
RUN python manage.py collectstatic --clear --noinput
