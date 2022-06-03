#!/bin/bash

service mongod start
cd /serve
./virt/bin/python src/run.py $1
