#! /bin/bash

# Rebuild the singleuser docker image

source .env

docker build -t $DOCKER_NOTEBOOK_IMAGE:dev ./singleuser