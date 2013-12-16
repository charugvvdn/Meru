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



d = {"snum": "AA:BB:CC:DD:00:DD","timestamp" : int(time.time()),"msgBody": {"controller": {"mac": "AA:BB:CC:DD:00:DD", "ip": "192.268.111.10","hostname": "MERU-CONTROLLER", "uptime": 324500000, "location": "SUNNYVALE","contact": "siby@merunetworks.com", "operState": "UP", "model": "MC1550", "swVersion": "6.0-157", "countrySettings": "US-PT", "alarms": [{"alarmType": "AP Down", "severity": "High", "timeStamp": 34546700000,"content": "Access Point AP-3 at time Wed Oct 16 08:39:37 2013"}], "aps": [{"mac": "OO:OC:E6:11:22:33", "ip": "192.168.11.76", "status": "UP", "id": a1, "uptime": 34556790000, "name": "Meru-Board-Room", "swVersion": "5.0-120", "model": "AP-330i", "rxBytes": random_with_N_digits(6), "txBytes": random_with_N_digits(5), "wifiExp": gen_wifi(), "wifiExpDescr": "string of max 30chars"},{"mac": "OO:OC:E6:11:12:33", "ip": "192.168.11.76", "status": "UP", "id": a2, "uptime": 34556790000, "name": "Meru-Board-Room", "swVersion": "5.0-120", "model": "AP-330i", "rxBytes": random_with_N_digits(6), "txBytes": random_with_N_digits(5), "wifiExp": gen_wifi(), "wifiExpDescr": "string of max 30chars"}], "clients": [{"mac": "AA:BB:CC:DD:00:AA","state": "associated", "apId": a1, "ip": "192.168.100.10", "clientType": "Mac", "rfBand": "11abgn", "ssid": "CORP_WIFI", "rxBytes": random_with_N_digits(5), "txBytes": random_with_N_digits(6),"wifiExp": gen_wifi(), "wifiExpDescr": "string of max 30chars"}, {"mac": "AA:BB:CC:DD:00:FF", "state": "associated","apId": a1, "ip": "192.168.100.44", "clientType": "iPhone", "rfBand": "11abgn", "ssid": "CORP_WIFI", "rxBytes": random_with_N_digits(7), "txBytes": random_with_N_digits(6), "wifiExp": gen_wifi(), "wifiExpDescr": "string of max 30chars"}]}}}

import json

sp = json.dumps(d)

with open('some4.txt', 'w') as f:
    f.write(sp)
