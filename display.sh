#!/bin/bash
# Build and run the whole website on this machine, then take it down again when you press control-c.
# The Next.js frontend builds inside Docker like the other services; nothing is prepared on the host.
clear
read -r -p "HySite DISPLAY Script, press any key to continue..."
# take any running containers offline
docker compose --profile api down
# build and run the API, both frontends and the nginx server
docker compose --profile api up --build
# use control-c to stop the website, then docker down is called
docker compose --profile api down || exit
echo " "
echo "completed: HySite DISPLAY Script"
