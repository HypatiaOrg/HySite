# HySite

A website and database for elemental abundance measurements of the Hypatia Catalog. 
This is a multi-service repository that contains all the data-sciences, API, and web development code.

# Update

You should be in the HySite directory that has the docker `compose.yaml` file

## Update 1/4: Run the data upload python script

To see all the options for this script
add the help flag, for example:
```bash
python backend/update.py --help
```

Note that the `--no-refresh-exo` fleag is used to prevent the script from downloading 
the exoplanet data from the NASA exoplanet archive.
Instead a cached copy of the data is used.

### Docker environment (option 1)
```bash
docker compose run --build --rm django-api python update.py
```

### Python environment (option 2)
```bash
python backend/update.py
```

## view the test version of the website on your local computer
```bash
docker compose pull
```

and then

```bash
docker compose up --build
```

use `control-c` to stop the server and free up the terminal

## Update 2/4: Commit and push the changes to the repository in GitHub
Before rebuilding containers on the server,
all changes must be pushed to the GitHub Repository and must be on the main branch
or the caleb/no-api branch for the Web2py repository.

### optional: switch to a new branch
```bash
git checkout -b <branch-name>
````

for example, to switch to a branch called `update-data`
```bash
git checkout -b update-data
```

### check file changes with git status
```bash
git status
```

### Add the changes to the git repository
`<files>`  is a list of files that you want to commit,
these could be changed files, new files, or deleted files.
```bash
git add <files>
```

### Verify that the changes have been staged (added)
```bash  
git status
```

### commit the changes with a message
```bash
git commit -m "A message about the changes"
```

### push the changes to the repository
```bash
git push
```

### optional 1: make a pull request on GitHub
Go to the GitHub repository and make a pull request from the branch you pushed to the main branch.
https://github.com/HypatiaOrg/HySite/pulls

Follow the prompts to create the pull request.

It is possible to merge the changes directly from the GitHub interface,
and then delete the branch after the changes have been merged.

### optional 2: merge the changes into the main branch
```bash
git checkout main
git merge <branch-name>
```
and then push the changes to the repository
```bash
git push
```

## Update 3/4: Publish the data to a public database

This is the database used by the live website, 
it makes a copy of the data in the used as a test database 
and moves it to the public database.

This is the same files as the the data upload script,
but no we add the `--publish` flag to the command
to run a separate definition that updates the public database.


### Docker environment (option 1)
This requires that any changes have been pushed to the repository
and are on the main branch or the caleb/no-api branch for the Web2py repository.

```bash
docker compose run --rm django-api python update.py --publish
```

### Python environment (option 2)

```bash
python backend/update.py --publish
```

## Update 4/4: Finish the Update database

### SSH into the server

```bash
ssh hysite
```

The following commands for options 1 and 2 are run on the server. 

### rebuild the docker containers (option 1)

Have your GitHub username and token ready for the prompts.
```bash
/home/ubuntu/HySite/scripts/update.sh
```

### restart the containers only (option 2)
Consider this options if you have already run the `update.sh` script
and do not want to rebuild the containers.

```bash
ssh hysite "docker compose --file /home/ubuntu/HySite/compose.yaml restart"
```

### exit the connection

```bash
exit
```

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

### Clone the data repository
This is a private repository, 
you will need to be added to the HypatiaOrg organization to access it.

```bash
cd HySite/backend/hypatia
git clone https://github.com/HypatiaOrg/HyData
cd ../../
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

## Build the docker containers
You should be in the HySite directory that has the docker `compose.yaml` file

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
