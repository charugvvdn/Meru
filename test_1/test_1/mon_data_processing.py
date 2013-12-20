from django.core.management import setup_environ
import settings
setup_environ(settings)
import MySQLdb as mydb
from pymongo import MongoClient
import datetime as d
import time

'''
    Standalone script to process mongodb data for mysql.
'''

db = mydb.connect(host='localhost', user='root', db='nms_test_1', passwd='root')
cursor = db.cursor()
t_stmp = int(time.time())

def main():
    db = MongoClient()['nms']
    doc_list = []
    controllers = []
    mon_data = []
    alarm_list = []
    alarm_mon_data = []
    ap_list = []
    ap_mon_data = []
    client_list = []
    client_mon_data = []
    ap_info = {}

    offset  = d.datetime.utcnow() - d.timedelta(minutes=1)
    start_time = int((offset - d.datetime(1970, 1, 1)).total_seconds())
    end_time  = int((d.datetime.utcnow() - d.datetime(1970, 1, 1)).total_seconds())

    #Doc query to fetch last 1 minute's monitoring data
    c = db.devices.find({ "timestamp" : { "$gt" : start_time, "$lt" : end_time}}).\
            sort("timestamp", -1)

    for doc in c:
        doc_list.append(doc)

    for doc in doc_list:
        if doc['snum'] not in controllers:
            controllers.append(doc['snum'])
            mon_data.append(doc)
        else:
            continue

    for doc in mon_data:
        alarms = []
        aps = []
        clients = []
        alarms = doc.get('msgBody').get('controller').get('alarms')
        aps = doc.get('msgBody').get('controller').get('aps')
        clients = doc.get('msgBody').get('controller').get('clients')
        for alarm in alarms:
            alarm['c_mac'] = doc['snum']
        for ap in aps:
            ap['c_mac'] = doc['snum']
            ap_info[ap['id']] = ap['mac']
        for client in clients:
            client['ap_mac'] = ap_info[client['apId']]
        ap_list.append(aps)
        alarm_list.append(alarms)
        client_list.append(clients)
    alarm_mon_data = traverse(alarm_list, alarm_mon_data)
    ap_mon_data = traverse(ap_list, ap_mon_data)
    client_mon_data = traverse(client_list, client_mon_data)
    insert_alarm_data(alarm_mon_data)
    insert_ap_data(ap_mon_data)
    insert_client_data(client_mon_data)

def insert_alarm_data(alarm_list):
    alarm_data = []
    t = ()
    for alarm in alarm_list:
        t = (str(alarm['c_mac']), str(alarm['alarmType']), str(alarm['severity']), \
                str(alarm['timeStamp']), str(alarm['content']), \
                4501, t_stmp, 0, 1)
        alarm_data.append(t)
        t = ()
    cursor.executemany(
        '''INSERT INTO alarm (controller_mac_address, alarm_type, severity,\
                timestamp, content, cid, updated_on, is_read, sent_status) \
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)''', alarm_data
        )
    db.commit()

    return "Success msg from alarm_data\n"

def insert_ap_data(ap_list):
    ap_data = []
    t = ()
    for ap in ap_list:
        t = (str(ap['mac']), str(ap['c_mac']), str(ap['ip']), str(ap['status']), \
                str(ap['uptime']), str(ap['name']), 'Default', str(ap['model']), str(ap['id']), \
                str(ap['swVersion']), str(ap['rxBytes']), str(ap['txBytes']), \
                str(ap['wifiExp']), str(ap['wifiExpDescr']), 4600, t_stmp)
        ap_data.append(t)
        t = ()
    cursor.executemany(
        '''INSERT INTO access_point (ap_mac_address, controller_mac_address,\
             ip_address, status, uptime, name, location, model, ap_id, ap_sw, \
             rxBytes, txBytes, wifiExp, wifiExpDescr, cid, updated_on)\
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)''',
            ap_data
        )
    db.commit()

    return "Succ from ap_data"

def insert_client_data(client_list):
    client_data = []
    t = ()
    for client in client_list:
        t = (str(client['mac']), str(client['ap_mac']), str(client['ip']), str(client['clientType']), \
                str(client['rfBand']), str(client['ssid']), str(client['rxBytes']), str(client['txBytes']), \
                str(client['wifiExp']), str(client['wifiExpDescr']), 4600, t_stmp)
        client_data.append(t)
        t = ()
    cursor.executemany(
            '''INSERT INTO ap_client (client_mac_address, ap_mac_address, client_ip_address, \
                type, RFband, SSID, rxBytes, txBytes, wifiExp, wifiExpDescr, cid, updated_on)\
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)''',
                client_data
        )
    db.commit()

    return "Succ from client_data"

def traverse(obj, l):
    if hasattr(obj, '__iter__'):
        for o in obj:
            if isinstance(o, dict):
                l.append(o)
            else:
                traverse(o, l)
    return l


if __name__ == "__main__":
    main()
