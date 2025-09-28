#!/bin/bash
clear
read -r -p "HySite DISPLAY Script, press any key to continue..."
# take and currently running containers offline and delete any volumes from the last build
docker compose --profile api --profile next down
# bring up the the backend and nginx server
docker compose --profile api up --build --detach || exit
echo "Build a local API (backend) and NGINX-server completed, building the frontend..."
# build the frontend on the local machine (we need the cache from this for the docker-build later)
cd frontend || exit
# remove the .next folder to ensure a clean build
rm -rf .next || return
# copy production environment variables
rm .env.production || return
cp .env.display .env.production || exit
# update the packages in package-lock.json (this requires node https://nodejs.org/en/download/package-manager)
npm update || exit
cd ../ || exit
# copy image files for optimization in the Next build time
curl --output-dir ./frontend/public/ -O http://localhost/hypatia/api/static/plots/abundances.png
# build in the docker container
echo -r -p "Local Build for frontend completed (needed for fetch-cache), launching the test-website..."
docker compose build next-frontend || exit
# stop here to look for error messages
echo " "
read -r -p "Frontend Build completed, press any key to launch the test-website and continue..."
# launch the test website
docker compose --profile api --profile next up
# use control-c to stop the test website, then docker down is called
docker compose --profile api --profile next down || exit
echo " "
echo "completed: HySite DISPLAY Script"
