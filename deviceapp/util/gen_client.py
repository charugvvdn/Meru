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



d = {"controller_mac": "10:20:30:40:50:df", "lower_snum" : "10:20:30:40:50:df", "timestamp" : int(time.time()),"clients": {"mac": "AA:BB:CC:DD:00:66","state": "associated", "apId": a1, "ip": "192.168.100.10", "clientType": "X-Type", "rfBand": "11abgn", "ssid": "CORP_WIFI", "rxBytes": 2000, "txBytes": 2000,"wifiExp": gen_wifi(), "wifiExpDescr": "string of max 30chars"}}

import json

sp = json.dumps(d)

with open('some4.txt', 'w') as f:
    f.write(sp)
