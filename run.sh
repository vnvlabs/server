#!/bin/bash

# First step is to create a virtual python env and install the requirments
virtualenv virt
virt/bin/pip install -r requirements.txt

# Second step is to build the serve docker image. This just install mongodb inside the base image and
# copies over the launch script:
docker build -f docker/Dockerfile -t vnv_serve --build-arg VNV_BASE_IMAGE=$1 ./docker 

#Get a list of files needed by theia so we can forward them 
docker run --rm -it vnv_serve ls /theia/lib > theia_forwards
docker run --rm -it vnv_serve ls /paraview/share/paraview-5.10/web/visualizer/www > pv_forwards
#last step is to run the thing
virt/bin/python src/run.py config.json ./theia_forwards ./pv_forwards
