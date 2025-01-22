#!/bin/bash
clear
cd /home/ubuntu/HySite || return
echo "Updating HySite repos, a pipeline, database, and website for HypatiaCatalog.com"
git pull origin main || exit
git submodule update --recursive || exit
echo "Updating the docker containers"
docker compose pull || exit
docker compose build || exit
docker compose up --detach || exit
read -r -p "Check the website then Press enter to continue deleting the docker cache"
docker system prune --all --force || exit
echo "Updates completed"
