# HySite

A website and database for elemental abundance measurements of the Hypatia Catalog. 
This is a multi-service repository that contains all the data-sciences, API, and web development code.

# Installation

## Prerequisites
Docker is required to run the services.
Git is required to clone the repository.

## Clone and enter the repository
```bash
git clone https://github.com/HypatiaOrg/HySite
```

## Clone the data repository
```bash
cd HySite/backend/hypatia
git clone https://github.com/HypatiaOrg/HyData
```

## Clone Web2py repository
```bash
cd ../../
git clone https://github.com/HypatiaOrg/WebServer -b caleb/no-api --single-branch web2py
```