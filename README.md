# HySite

A website and database for elemental abundance measurements of the [HypatiaCatalog.com](https://hypatiacatalog.com). 
This is a multi-service repository that contains all the data-sciences, API, and web development code.

We are migrating the documentation to our [GitHub wiki](https://github.com/HypatiaOrg/HySite/wiki),
# Update



# Installation

## Prerequisites
Docker is required to run the services.
https://docs.docker.com/engine/install/

Git is required to clone the repository.
https://git-scm.com/downloads

## Clone the repositories

### Clone and enter the repository
```bash
git clone https://github.com/HypatiaOrg/HySite
```

### Initialize the submodules for Web2py


This repository uses submodules to include the web2py framework,
and so does [web2py](https://www.web2py.com/) ([github.com/web2py/web2py](https://github.com/web2py/web2py)) itself.

> [!WARNING]
> Web2py is an outdated framework, 
> but in 2025 it is still being maintained.
> The successor to web2py is [Py4Web](https://py4web.com/).
> However, the HypatiaCatalog project 
> may upgrade to a JavaScript framework in the future
> (see [Issue 19](https://github.com/HypatiaOrg/HySite/issues/19)),
> or use the Django-Python framework that is currently being used for the API.


```bash
git submodule update --init --recursive
```

> [!NOTE]
> More on git submodules can be found at 
> [git-scm.com/book/en/v2/Git-Tools-Submodules](https://git-scm.com/book/en/v2/Git-Tools-Submodules).
> Submodules can be initialized with `git submodule add <repository> <path>`, for example:
> ```bash
> git submodule add https://github.com/web2py/web2py frontend-web2py/web2py
> ```

### Clone the HyData repository
This is a private repository, 
you will need to be added to the HypatiaOrg organization to access it.

This is needed for operations and development of the HypatiaCatalog data processing pipeline.

```bash
cd HySite/backend/hypatia
git clone https://github.com/HypatiaOrg/HyData
cd ../../
```
## Configuration (.env) file
The is a number of possible configurations the docker containers can use
make parts of the website or the whole website, 
or just the data processing pipeline in a Jupyter notebook.
Many of this configuration are set in the `.env` file in the root of the repository.
This file is never committed to the repository, and can contain sensitive information.

> [!TIP]
> The see the `example.env` file for an example of the configuration options.

> [!NOTE] 
> Many of the configuration options have defaults that are in the `compose.yaml`
> at the root of the repository. 
> When a variable is not present in the `.env` file, the default value is used.

### Website Frontend only

This is the default configuration, no `.env` file is needed.
An empty `.env` will also has this configuration.

```bash
docker compose up --build
```

### Website and API
If you have at a minimum *read* credentials to the HypatiaCatalog MongoDB database,
then you can run a local website that calls with a local API,
but still use the hypatiacatalog.com MongoDB server.

```text
COMPOSE_PROFILES=api
CONNECTION_STRING=mongodb://read_test:DKg%40%5E_c@hypatiacatalog.com:27017
```

> [!NOTE]
> The `CONNECTION_STRING` will be provided for you by the database administrator.

> [!WARNING]
> The `CONNECTION_STRING` should not be committed to the repository.

The `COMPOSE_PROFILES` variable is used to select the services that are run,
so deploy locally with the following command:
```bash
docker compose up --build
```
### Website and API with a local MongoDB server
This requires no credentials to the HypatiaCatalog MongoDB database
since the local website and local API will use a local MongoDB server.

> [!WARNING]
> The first time this docker is called this,
> creates the Root username and password for the MongoDB database.

```text
COMPOSE_PROFILES=db,api
MONGO_USERNAME=username
MONGO_PASSWORD="your-50-character-or-more-password-here"
MONGO_HOSTNAME=mongoDB
# RESTART_POLICY=always
# DEGUG=false
# VOLUME_SPECIFICATION=ro
# READ_ONLY=true
# LOCAL_PORT=8000
# MONGO_DATABASE=public
# USE_EXTERNAL_NETWORK=true
```

> [!TIP]
> The commented out values differ from 
> the defaults in the `compose.yaml` and can
> be used to override the defaults. 
> The commented out values are recommended for a remote server deployment.

Deploy with the following command:
```bash
docker compose up --build
```

### Jupyter notebook
This requires database access, which could be read or write 
to the hypatiacatalog.com MongoDB database or a local MongoDB server (see above).

```text
JUPYTER_TOKEN="your-50-character-or-more-token-for-jupyter-notebook"
MONGO_USERNAME=username
MONGO_PASSWORD="your-50-character-or-more-password-here"
# MONGO_HOSTNAME=mongoDB # use this line for a local MongoDB server
MONGO_HOSTNAME=hypatiacatalog.com
```

Use:
```bash
docker compose up --build ipython
```

> [!NOTE]
> Run only the mongoDB service stand-alone with the following command:
> ```bash
> docker compose up mongo-db
> ```
> Or together with the Jupyter notebook service with the following command:
> ```bash
> docker compose up --build mongo-db ipython
> ```

## Docker

We use docker to manage the services that make up the website
and also to run the data processing pipeline.

Navigate your terminal the `HySite` directory that has the docker `compose.yaml` file

### Check that the docker daemon is running
```bash
docker version
```

You should see the version of the docker *Client* and **Server**.

an example output might look like this, not the you will only see the 
Client version if the docker daemon is not running. 
Start the docker daemon DockerDesktop on your computer https://docs.docker.com/desktop/, 
or starting the docker service a linux server https://docs.docker.com/engine/daemon/start/
```
Client:
 Version:           27.3.1
 API version:       1.47
 Go version:        go1.22.7
 Git commit:        ce12230
 Built:             Fri Sep 20 11:38:18 2024
 OS/Arch:           darwin/arm64
 Context:           desktop-linux

Server: Docker Desktop 4.35.1 (173168)
 Engine:
  Version:          27.3.1
  API version:      1.47 (minimum version 1.24)
  Go version:       go1.22.7
  Git commit:       41ca978
  Built:            Fri Sep 20 11:41:19 2024
  OS/Arch:          linux/arm64
  Experimental:     false
 containerd:
  Version:          1.7.21
  GitCommit:        472731909fa34bd7bc9c087e4c27943f9835f111
 runc:
  Version:          1.1.13
  GitCommit:        v1.1.13-0-g58aa920
 docker-init:
  Version:          0.19.0
  GitCommit:        de40ad0

```



### pull new versions of the images
This is the way to update NGINX and MongoDB images
```bash
docker compose pull
```

### To run in the background
```bash
docker compose up --build --detach
```

### To run in the foreground and view logs actively
```bash
docker compose up --build
```

use `control-c` to exit and free up the terminal

### to close the containers and free up resources
```bash
docker compose down
```

### delete all cached data not being used by running containers

Do this to free up space on your computer or the website server. 
```bash
docker system prune --all --force
```

## SSH setup 

### SSH confile file
The ssh command `ssh hysite`, 
used in this file expects that you have the server in your ssh config file
at `~/.ssh/config` with the following lines

```
Host hysite
    User ubuntu
    Hostname hypatiacatalog.com
    ForwardX11 yes
    IdentityFile ~/.ssh/hysite-ssh-key.pem
```

Open the file with the editor and add the lines above.

### SSH key file
The key file is not included in the repository, 
you will need to get it from the server administrator.

It may not come with the correct permissions,
set it to be read only with the following command

```bash
sudo chmod 400 ~/.ssh/hysite-ssh-key.pem
```

### SSH into the server

```bash
ssh hysite
```

The first time you connect, you will be asked to accept the server key.
select `yes` to continue.

logout with the command `exit`.

# Maintenance

## Clean up git branches

These instructions are based on this Medium post:
[A simple way to clean up your git project branches](https://medium.com/@FlorentDestrema/a-simple-way-to-clean-up-your-git-project-branches-283b87478fbc)

There can be a lot of local branches in the repository
that were merged into the `main` branch
and are no longer needed.

```bash
git branch -d $(git branch --merged=main | grep -v main)
```


Then remove the branches that are not in the remote GitHub repository with:
```bash
git fetch --prune
```
