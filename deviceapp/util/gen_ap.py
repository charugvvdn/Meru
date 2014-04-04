import time
import random
from random import randint

def gen_rand():
    ap_id = random.random()* random.random()* 100 * random.random() /  random.random()
    if int(ap_id):
        return int(ap_id)
    else:
        return gen_rand()
a1 = gen_rand()
a2 = gen_rand()

def gen_wifi():
    wifi = random.random()* random.random()* 100 * random.random() /  random.random()
    if 0 <= int(wifi) <= 100 :
        return int(wifi)
    else:
        return gen_wifi()

def random_with_N_digits(n):
#    range_start = 10**(n-1)
#    range_end = (10**n)-1
#    return randint(range_start, range_end)
    if n%2:
        return 1000
    else:
        return 3000



d = {"lower_snum" : "10:20:30:40:50:CC", "timestamp" : int(time.time()), "controller_mac" : "10:20:30:40:50:CC","aps": {"mac": "OO:OC:E6:11:22:FF", "ip": "192.168.11.76", "status": "Down", "id": a1, "uptime": 34556790000, "name": "Meru-Board-Room", "swVersion": "5.0-120", "model": "AP-330i", "rxBytes": random_with_N_digits(6), "txBytes": random_with_N_digits(5), "wifiExp": gen_wifi(), "wifiExpDescr": "string of max 30chars"}}

import json

sp = json.dumps(d)

with open('some4.txt', 'w') as f:
    f.write(sp)
