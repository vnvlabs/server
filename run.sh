#!/bin/bash


# First step is to build the serve docker image. This just install mongodb inside the base image and
# copies over the launch script:

docker build -t vnv_serve --build-arg VNV_BASE_IMAGE=$1 . 

# Next step is to create a virtual python env and install the requirments
virtualenv virt
virt/bin/pip install -r src/requirements.txt

#last step is to run the thing
virt/bin/python src/run.py config.json
