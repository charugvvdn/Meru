import MySQLdb as mydb
from pymongo import MongoClient
import datetime as d
import time

'''
    Standalone script to process mongodb data for mysql.
'''

db = mydb.connect(host='localhost', user='root', db='nms_test_1_clone', passwd='root')
#cursor = db.cursor()
t_stmp = int(time.time())

def find_controller(controller_mac=None):
    cursor = db.cursor()
    if controller_mac:
        query = "SELECT `controller_id`, `controller_mac` " \
		 "FROM `meru_controller` " \
		 "WHERE `controller_mac` = %s LIMIT 1"
        
        cursor.execute(query, (controller_mac))
        result = cursor.fetchone()
        cursor.close()
        return result

def make_ready_controller():
    pass        

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

    offset  = d.datetime.utcnow() - d.timedelta(minutes=2)
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
    insert_ap_list = []
    update_ap_list = []

    for doc in reversed(mon_data):
        alarms = []
        aps = []
        clients = []
        t_stmp = doc.get('timestamp')
        aps = doc.get('msgBody').get('controller').get('aps')
        alarms = doc.get('msgBody').get('controller').get('alarms')
        #search for the controller id
        controller_id = find_controller(doc['snum'])

        for ap in aps:
            ap['c_mac'] = doc['snum']
            ap['c_id'] = controller_id[0]
            ap_info[ap['id']] = ap['mac']
            if find_ap(ap['mac']):
                update_ap_list.append(ap)
            else:
                insert_ap_list.append(ap)

        for alarm in alarms:
            alarm['c_mac'] = controller_id[1]
        alarm_list.append(alarms)

    alarm_mon_data = traverse(alarm_list, alarm_mon_data)
    insert_alarm_data(alarm_mon_data)

    if len(update_ap_list):
        u_ap_mon_data = traverse(update_ap_list, ap_mon_data)
        update_ap_data(u_ap_mon_data)

    if len(insert_ap_list):
        i_ap_mon_data = traverse(insert_ap_list, ap_mon_data)
        insert_ap_data(i_ap_mon_data)

def insert_alarm_data(alarm_list):
    cursor = db.cursor()
    alarm_data = make_ready_alarm(alarm_list)
    cursor.executemany(
    """
    INSERT INTO `meru_alarm`
    (`alarm_cmac`, `alarm_type`, `alarm_severity`, 
    `alarm_ts`, `alarm_content`, `alarm_status`)
    VALUES (%s,%s,%s,%s,%s,%s)
    """,alarm_data
        )
    db.commit()
    cursor.close()
    print "Succ from insert alarm_data"

def make_ready_alarm(alarm_list):
    alarm_data = []
    for alarm in alarm_list:
        t = (alarm['c_mac'], alarm['alarmType'], alarm['severity'],
                alarm['timeStamp'], alarm['content'], 0)
        alarm_data.append(t)
        t = ()
    return alarm_data

def find_ap(ap_mac):
    cursor = db.cursor()
    if ap_mac:
        query = "SELECT COUNT(*) " \
                 "FROM `meru_ap` " \
                 "WHERE `ap_mac` = %s LIMIT 1"

        cursor.execute(query, (ap_mac))
        result = cursor.fetchone()
        cursor.close()
        if result[0]:
            return True
        return False
    
def make_ready_ap(ap_list, update=True):
    ap_data = []
    if update:
        for ap in ap_list:
             status = 1 if ap['status'].lower() == "up" else 0
             t = (ap["name"], ap["c_id"], ap["mac"], ap["ip"], ap["model"], ap["rxBytes"], ap["txBytes"],
                ap['wifiExp'], ap["wifiExpDescr"], status, ap["c_mac"], ap["mac"])

             ap_data.append(t)
             t = ()
    else:
        for ap in ap_list:
             status = 1 if ap['status'].lower() == "up" else 0
             t = (ap["name"], ap["c_id"], ap["mac"], ap["ip"], ap["model"], ap["rxBytes"], ap["txBytes"],
                ap['wifiExp'], ap["wifiExpDescr"], status, ap["c_mac"])

             ap_data.append(t)
             t = ()
    return ap_data

def update_ap_data(ap_list):
    cursor = db.cursor()
    ap_data = make_ready_ap(ap_list, update=True)
    cursor.executemany(
	"""
	UPDATE `meru_ap`
	SET `ap_name`=%s, `ap_cid_fk`=%s, `ap_mac`=%s, `ap_ip`=%s, `ap_model`=%s,
	    `ap_rx`=%s, `ap_tx`=%s, `ap_wifiexp`=%s, `ap_wifiexp_desc`=%s,
	    `ap_status`=%s, `controller_mac`=%s
	WHERE `ap_mac`=%s
	""", ap_data
    )
    db.commit()
    cursor.close()
    print "Succ from update ap_data"

def insert_ap_data(ap_list):
    cursor = db.cursor()
    ap_data = make_ready_ap(ap_list, update=False)
    cursor.executemany(
	"""
	INSERT INTO `meru_ap`
	(`ap_name`, `ap_cid_fk`, `ap_mac`, 
	`ap_ip`, `ap_model`, `ap_rx`, `ap_tx`, `ap_wifiexp`, 
	`ap_wifiexp_desc`, `ap_status`, `controller_mac`)
	VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
	""",ap_data
        )
    db.commit()
    cursor.close()
    print "Succ from insert ap_data"
'''
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
            """INSERT INTO ap_client (client_mac_address, ap_mac_address, client_ip_address, \
                type, RFband, SSID, rxBytes, txBytes, wifiExp, wifiExpDescr, cid, updated_on)\
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                client_data
        )
    db.commit()

    return "Succ from client_data"
'''
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
