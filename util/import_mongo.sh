#!/bin/sh

python gendata.py
mongoimport --db nms --collection devices --type json --file some4.txt
