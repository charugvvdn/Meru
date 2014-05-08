import MySQLdb as mydb
from pymongo import MongoClient
import datetime as d
import time
import settings

'''
    Standalone script to process mongodb data for mysql.
'''
try:
    db = mydb.connect(host='localhost', user='root', db=settings.DATABASES['meru_cnms_sitegroup']['NAME'], passwd='root')
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
            print controller['swVersion'].lower().strip()
            if controller['operStat'].lower().strip() == "enabled" or controller['operStat'].lower().strip() == "up":
                status = 1
                t = (status, controller['swVersion'].lower().strip(), controller["mac"])
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
        `device_opstatus`=%s, `device_swversion`=%s 
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
            t = (client['mac'], client['rxBytes'], client['txBytes'],client['rssi'],client['mac'])
            client_data.append(t)
            t = ()
    else:
        for client in client_list:
            t = (client['mac'],client['rxBytes'], client['txBytes'],client['rssi'])
            client_data.append(t)
            t = ()
    return client_data

def update_client_data(client_list):
    cursor = db.cursor()
    client_data = make_ready_client(client_list, True)
    cursor.executemany(
    """
    UPDATE `meru_client`
    SET `client_mac` = %s, `client_rx` = %s, `client_tx` = %s, `client_ssid` = %s
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
    (`client_mac`,`client_rx`, `client_tx`, `client_ssid`)
    VALUES (%s,%s,%s,%s)
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
    c = db.devices.find({"msgBody.msolo":{"$exists":1}, "timestamp" : { "$gt" : start_time, "$lt" : end_time}}).\
            sort("timestamp", -1)

    for doc in c:
        doc_list.append(doc)

    for doc in doc_list:
        if doc['snum'] not in controllers:
            controllers.append(doc['snum'])
            mon_data.append(doc)

    insert_ap_list = []
    update_ap_list = []
    
    insert_client_list = []
    update_client_list = []

    controller_list = []

    for doc in reversed(mon_data):
        alarms = []
        clients = []
        msolo = []

        t_stmp = doc.get('timestamp')
        
        alarms = doc.get('msgBody').get('msolo').get('alarms')
        clients = doc.get('msgBody').get('msolo').get('clients')
        controllers = doc.get('msgBody').get('msolo')

        #search for the controller id
        controller_id = find_controller(doc['snum'])

        controller = {}
        controller["ip"] = controllers["ip"]
        controller["hostname"] = controllers["hostname"]
        controller["uptime"] = controllers["uptime"]
        controller["location"] = controllers["location"]
        controller["contact"] = controllers["contact"]
        controller["operStat"] = controllers["operState"]
        controller["swVersion"] = controllers["swVersion"]
        controller["countrySettings"] = controllers["countrySettings"]
        controller["mac"] = controllers["mac"]
        controller_list.append(controller)

        
        for alarm in alarms:
            alarm['c_mac'] = controller_id[1]
            alarm_list.append(alarms)

        unique_clients = {}

        for client in clients:
            if client['mac'] not in unique_clients:

                unique_clients[client['mac']] = True
                if find_client(client['mac']):
                    update_client_list.append(client)
                else:
                    insert_client_list.append(client)

    print "Final controller list"
    print controller_list
    alarm_mon_data = traverse(alarm_list, alarm_mon_data)

    if len(controller_list):
        update_controller(controller_list)

    if len(alarm_mon_data):
        insert_alarm_data(alarm_mon_data)

    if len(update_client_list):
        update_client_data(update_client_list)

    if len(insert_client_list):
        insert_client_data(insert_client_list)


if __name__ == "__main__":
        main()

