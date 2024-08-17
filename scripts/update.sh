#!/bin/bash
clear
echo "Updating HySite repos, a pipeline, database, and website for HypatiaCatalog.com"
git pull origin main
cd backend/hypatia/HyData && git pull origin main && cd ../../../
cd web2py && git pull origin caleb/no-api && cd ../

