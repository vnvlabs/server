#!/bin/bash

# First step is to create a virtual python env and install the requirments
virtualenv virt
virt/bin/pip install -r requirements.txt
virt/bin/python src/run.py config.json
