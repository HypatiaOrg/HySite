#!/bin/bash
clear
echo "Updating HySite repos, a pipeline, database, and website for HypatiaCatalog.com"
git pull origin main
cd backend/hypatia/HyData && git pull origin main && cd ../../../
cd web2py && git pull origin caleb/no-api && cd ../
echo "Updating the docker containers"
docker compose pull
docker compose build
docker compose down
docker compose up --detech
read -p -r "Check the website then Press enter to continue deleting the docker cache"
docker system prune --all --force
echo "Done"