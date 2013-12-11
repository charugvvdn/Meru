#!/bin/sh

python /home/charu/gendata.py
mongoimport --db nms --collection devices --type json --file /home/charu/some4.txt
