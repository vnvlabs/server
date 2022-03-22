#!/bin/bash


# First step is to build the serve docker image. This just install mongodb inside the base image and
# copies over the launch script:
cd src 

docker build -t vnv_serve --build-arg VNV_BASE_IMAGE=$1 . 

# Next step is to create a virtual python env and install the requirments
virtualenv virt
virt/bin/pip install -r requirements.txt

#last step is to run the thing
virt/bin/python run.py $1
