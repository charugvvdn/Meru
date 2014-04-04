#!/bin/sh

python gen_ap.py
mongoimport --db nms --collection device_aps --type json --file some4.txt
