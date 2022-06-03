#!/bin/bash

cd /serve
mongod -f /etc/mongodb.conf
./virt/bin/python src/run.py $1
