import MySQLdb as mydb
from pymongo import MongoClient
import datetime as d
import time
import settings

'''
    Standalone script to process mongodb data for mysql.
'''
try:
    db = mydb.connect(host='localhost', user='root', db=settings.DATABASES['meru_cnms_sitegroup']['NAME'], passwd=settings.DATABASES['meru_cnms_sitegroup']['PASSWORD'])
except mydb.Error, e:
    print e
#cursor = db.cursor()
t_stmp = int(time.time())

#to insert values from a dict to SQL.
#it is tough for a developer to map individual tuples
#to a perfect key (column) in database table
def insertFromDict(table, dict):
    """Take dictionary object dict and produce sql for 
    inserting it into the named table"""
    sql = 'INSERT INTO ' + table
    sql += ' ('
    sql += ', '.join(dict)
    sql += ') VALUES ('
    sql += ', '.join(map(dictValuePad, dict))
    sql += ');'
    return sql

def dictValuePad(key):
    return '%(' + str(key) + ')s'

# def exampleOfUse():
#     import MySQLdb
#     db = MySQLdb.connect(host='sql', user='janedoe', passwd='insecure', db='food') 
#     cursor = db.cursor()
#     insert_dict = {'drink':'horchata', 'price':10}
#     sql = insertFromDict("lq", insert_dict)
#     cursor.execute(sql, insert_dict)


def find_controller(controller_mac=None):
    cursor = db.cursor()
    if controller_mac:
        query = "SELECT `device_id`, `device_mac` FROM `meru_device` \
			WHERE `device_mac` = '%s' LIMIT 1" % controller_mac
        
        cursor.execute(query)
        result = cursor.fetchone()
        cursor.close()
        return result

def make_ready_controller(controller_list, update=True):
    controller_data = []
    if update:
        for controller in controller_list:
            if controller['operState'].lower().strip() == "enabled" or controller['operState'].lower().strip() == "up":
                status = 1
                t = (status, controller["mac"])
                controller_data.append(t)
                t = ()
    return controller_data

def update_controller(controller_list):
    cursor = db.cursor()
    controller_data = make_ready_controller(controller_list, update=True)
    cursor.executemany(
        """
        UPDATE `meru_device` 
        SET 
        `device_opstatus`=%s 
        WHERE `device_mac`=%s
        """, controller_data
    )
    db.commit()
    cursor.close()

    print "Updated Controller Data\n", controller_data
    print "Success from update controller data\n"

def make_ready_alarm(alarm_list):
    alarm_data = []
    for alarm in alarm_list:
        t = (alarm['c_mac'], alarm['alarmType'], alarm['severity'],
                alarm['timeStamp'], alarm['content'], 0)
        alarm_data.append(t)
        t = ()
    return alarm_data

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
    print "insert_alarm_data\n", alarm_data
    print "Succ from insert alarm_data\n"

def find_ap(ap_mac):
    cursor = db.cursor()
    print ap_mac
    if ap_mac:
        query = "SELECT COUNT(*)  \
                 FROM `meru_ap`  \
                 WHERE `ap_mac` ='%s' LIMIT 1" % ap_mac

        cursor.execute(query)
        result = cursor.fetchone()
        cursor.close()
        if result[0]:
	    print "ap_mac was found in db\n"
            return True
	print "ap_mac was not found in db\n"
        return False

def make_ready_ap(ap_list, update=True):
    timestamp = int(time.time())
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
                ap['wifiExp'], ap["wifiExpDescr"], status, ap["c_mac"], timestamp)

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
        `ap_status`=%s, `ap_controller_mac`=%s
    WHERE `ap_mac`=%s
    """, ap_data
    )
    db.commit()
    cursor.close()
    print "update_ap_data\n", ap_data
    print "Succ from update ap_data\n"

def insert_ap_data(ap_list):
    cursor = db.cursor()
    ap_data = make_ready_ap(ap_list, update=False)
    cursor.executemany(
    """
    INSERT INTO `meru_ap`
    (`ap_name`, `ap_cid_fk`, `ap_mac`, 
    `ap_ip`, `ap_model`, `ap_rx`, `ap_tx`, `ap_wifiexp`, 
    `ap_wifiexp_desc`, `ap_status`, `ap_controller_mac`, `ap_createdon`)
    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
    """,ap_data
        )
    db.commit()
    cursor.close()
    print "insert_ap_data\n", ap_data
    print "Succ from insert ap_data\n"

def find_client(client_mac):

    cursor = db.cursor()
    if client_mac:
        query = "SELECT COUNT(*) FROM `meru_client` \
                WHERE `client_mac` = '%s' LIMIT 1" % client_mac
        cursor.execute(query)
        result = cursor.fetchone()
        cursor.close()
        if result[0]:
            return True
        return False

def make_ready_client(client_list, update):
    client_data = []
    if update:
        for client in client_list:
            t = (client['mac'], client.get('ap_mac'), client['ip'], client['clientType'],
                client['rfBand'], client['ssid'], client['rxBytes'], client['txBytes'],
                client['wifiExp'], client['wifiExpDescr'], client['mac'])
            client_data.append(t)
            t = ()
    else:
        for client in client_list:
            t = (client['mac'], client.get('ap_mac'), client['ip'], client['clientType'],
                client['rfBand'], client['ssid'], client['rxBytes'], client['txBytes'],
                client['wifiExp'], client['wifiExpDescr'])
            client_data.append(t)
            t = ()
    return client_data

def update_client_data(client_list):
    cursor = db.cursor()
    client_data = make_ready_client(client_list, True)
    cursor.executemany(
    """
    UPDATE `meru_client`
    SET `client_mac` = %s, `client_apmac` = %s, `client_ip` = %s, `client_type` = %s, 
    `client_rfband` = %s, `client_ssid` = %s, `client_rx` = %s, `client_tx` = %s, 
    `client_wifiexp` = %s, `client_wifiexpdescr` = %s
    WHERE `client_mac`=%s
    """, client_data
    )
    db.commit()
    cursor.close()
    print "update_client_data\n", client_data
    print "Succ from update client_data\n"

def insert_client_data(client_list):
    cursor = db.cursor()
    client_data = make_ready_client(client_list, False)
    cursor.executemany(
    """
    INSERT INTO `meru_client`
    (`client_mac`, `client_apmac`, `client_ip`, 
    `client_type`, `client_rfband`, `client_ssid`, `client_rx`, `client_tx`, 
    `client_wifiexp`, `client_wifiexpdescr`)
    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
    """,client_data
        )
    db.commit()
    cursor.close()
    print "insert_client_data\n", client_data
    print "Succ from insert client_data\n"

def traverse(obj, l):
    if hasattr(obj, '__iter__'):
        for o in obj:
            if isinstance(o, dict):
                l.append(o)
            else:
                traverse(o, l)
    return l

def main():
    mongo_db = settings.DB
    unique_controller = []
    unique_clients = []
    unique_aps = []
    unique_client_device =[]
    unique_ap_device =[]

    controller_list = []
    update_client_list = []
    insert_client_list = []
    update_ap_list = []
    insert_ap_list = []
    alarm_list = []
    alarm_mon_data = []

    offset  = d.datetime.utcnow() - d.timedelta(minutes=1)
    start_time = int((offset - d.datetime(1970, 1, 1)).total_seconds())
    end_time  = int((d.datetime.utcnow() - d.datetime(1970, 1, 1)).total_seconds())
    qry = {}
    qry["timestamp"] =  {"$gt": start_time, "$lt": end_time }
    print qry

    #Doc query to fetch last 1 minute's monitoring data
    controller_cursor = mongo_db.device_controllers.find(qry).sort("timestamp", -1)
    client_cursor = mongo_db.device_clients.find(qry).sort("timestamp", -1)
    alarm_cursor = mongo_db.device_alarms.find(qry).sort("timestamp", -1)
    ap_cursor = mongo_db.device_aps.find(qry).sort("timestamp", -1)
    #another apcursor to use in client prcessing
    ap_cl_cursor = mongo_db.device_aps.find(qry).sort("timestamp", -1)


    
    for controller in controller_cursor:
        if controller['lower_snum'] not in unique_controller:
            unique_controller.append(controller['lower_snum'])
            controller['mac'] = controller['lower_snum']
            controller_list.append(controller)
    for ap in ap_cursor:
        if ap['lower_snum'] not in unique_ap_device:
            unique_ap_device.append(ap['lower_snum'])
            controller_id = find_controller(ap['lower_snum'])
            if 'aps' in ap:
                if ap['aps']['mac'] not in unique_aps:
                    unique_aps.append(ap['aps']['mac'])
                    ap['aps']['c_id'] = controller_id[0]
                    ap['aps']['c_mac'] = ap['lower_snum']

                    if find_ap(ap['aps']['mac']):
                        update_ap_list.append(ap['aps'])
                    else:
                        insert_ap_list.append(ap['aps'])

    for client in client_cursor:
        if client['lower_snum'] not in unique_client_device:
            unique_client_device.append(client['lower_snum'])
            if 'clients' in client:
                if client['clients']['mac'] not in unique_clients:
                    unique_clients.append(client['clients']['mac'])
                    if client.get('clients').get('apId') :
                        for ap in ap_cl_cursor :
                            if ap['aps']['id'] == client['clients']['apId']:
                                apmac = ap['aps']['mac']
                                client['clients']['ap_mac'] = apmac
                    else:
                        client['clients']['ap_mac'] = client['lower_snum']
                    client['clients']['clientType'] = client.get('clients').get('clientType') or 'unknown'
                    client['clients']['ip'] = client.get('clients').get('ip') or 0
                    client['clients']['rfBand'] = client.get('clients').get('rfBand') or ('band 11a' if client.get('clients').get('interface') == 'wlan1' else 'band 11b')
                    client['clients']['ssid'] = client.get('clients').get('ssid') or "None"
                    client['clients']['wifiExp'] = client.get('clients').get('wifiExp') or 0
                    client['clients']['wifiExpDescr'] = client.get('clients').get('wifiExpDescr') or "None"
                    if find_client(client['clients']['mac']):
                        update_client_list.append(client['clients'])
                    else:
                        insert_client_list.append(client['clients'])
    

    for cursor in alarm_cursor:
        for alarm in cursor['alarms']:
            
            controller_id = find_controller(cursor['lower_snum'])
            alarm['c_mac'] = controller_id[1]
            alarm_list.append(alarm)

    
    alarm_mon_data = traverse(alarm_list, alarm_mon_data)

    if len(controller_list):
        update_controller(controller_list)

    if len(alarm_mon_data):
        insert_alarm_data(alarm_mon_data)

    if len(update_client_list):
        update_client_data(update_client_list)

    if len(insert_client_list):
        insert_client_data(insert_client_list)

    if len(update_ap_list):
        #u_ap_mon_data = traverse(update_ap_list, ap_mon_data)
        update_ap_data(update_ap_list)

    if len(insert_ap_list):
        #i_ap_mon_data = traverse(insert_ap_list, ap_mon_data)
        insert_ap_data(insert_ap_list)
    db.close();

if __name__ == "__main__":
        main()

