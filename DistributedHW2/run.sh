#!/usr/bin/env bash

Aug1=$1

python3 server.py $1 > log.dat &
python3 client.py $1
