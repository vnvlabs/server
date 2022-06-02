#!/bin/bash

service mongodb start

cd /serve
./virt/bin/python src/run.py $1
