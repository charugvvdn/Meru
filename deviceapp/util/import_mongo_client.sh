#!/bin/sh

python gen_client.py
mongoimport --db nms --collection device_clients --type json --file some4.txt
