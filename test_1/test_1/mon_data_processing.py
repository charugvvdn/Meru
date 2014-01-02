import MySQLdb as mydb
from pymongo import MongoClient
import datetime as d
import time

'''
    Standalone script to process mongodb data for mysql.
'''

db = mydb.connect(host='localhost', user='root', db='meru_cnms', passwd='zaqwsxCDE')
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
        query = "SELECT `controller_id`, `controller_mac` " \
         "FROM `meru_controller` " \
         "WHERE `controller_mac` = %s LIMIT 1"
        
        cursor.execute(query, (controller_mac))
        result = cursor.fetchone()
        cursor.close()
        return result

def make_ready_controller(controller_list, update=True):
    controller_data = []
    if update:
        for controller in controller_list:
             status = 1 if controller['operState'].lower() == "enabled" or \
                            controller['operState'].lower() == "up" else 0
             t = (
                controller["ip"],
                controller["hostname"],
                controller["uptime"],
                controller["location"],
                controller["contact"], 
                controller["operState"], 
                controller["model"],
                controller["swVersion"], 
                controller["countrySettings"],
                t_stmp,
                status,
                controller["mac"]
                )

             controller_data.append(t)
             t = ()
    return controller_data

def update_controller(controller_list):
    cursor = db.cursor()
    controller_data = make_ready_controller(controller_list, update=True)
    cursor.executemany(
        """
        UPDATE `meru_controller` 
        SET 
        `controller_ip`=%s,
        `controller_hostname`=%s,
        `controller_uptime`=%s,
        `controller_location`=%s,
        `controller_contact`=%s,
        `controller_op_state`=%s,
        `controller_model`=%s,
        `controller_swversion`=%s,
        `controller_country_settings`=%s,
        `controller_modifiedon`=%s,
        `controller_opstatus`=%s 
        WHERE `controller_mac`=%s
        """, controller_data
    )
    db.commit()
    cursor.close()

    print "Updated Controller Data\n", controller_data
    print "Success from Controller Data Update"

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
    print "Succ from insert alarm_data"

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
    print "update_ap_data\n", ap_data
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
    print "insert_ap_data\n", ap_data
    print "Succ from insert ap_data"

def find_client(client_mac):
    cursor = db.cursor()
    if client_mac:
        query = "SELECT COUNT(*) FROM `meru_client` \
                WHERE `client_mac` = %s LIMIT 1"
        cursor.execute(query, (client_mac))
        result = cursor.fetchone()
        cursor.close()
        if result[0]:
            return True
        return False

def make_ready_client(client_list, update):
    client_data = []
    if update:
        for client in client_list:
            t = (client['mac'], client['ap_mac'], client['ip'], client['clientType'],
                client['rfBand'], client['ssid'], client['rxBytes'], client['txBytes'],
                client['wifiExp'], client['wifiExpDescr'], client['mac'])
            client_data.append(t)
            t = ()
    else:
        for client in client_list:
            t = (client['mac'], client['ap_mac'], client['ip'], client['clientType'],
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
    print "Succ from update client_data"

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
    print "Succ from insert client_data"

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

    insert_ap_list = []
    update_ap_list = []
    
    insert_client_list = []
    update_client_list = []

    controller_list = []

    for doc in reversed(mon_data):
        alarms = []
        aps = []
        clients = []
        controllers = []

        t_stmp = doc.get('timestamp')
        
        aps = doc.get('msgBody').get('controller').get('aps')
        alarms = doc.get('msgBody').get('controller').get('alarms')
        clients = doc.get('msgBody').get('controller').get('clients')
        controllers = doc.get('msgBody').get('controller')

        #search for the controller id
        controller_id = find_controller(doc['snum'])

        for cont in controllers:
            controller = {}

            controller["ip"] = cont["ip"]
            controller["hostname"] = cont["hostname"]
            controller["uptime"] = cont["uptime"]
            controller["location"] = cont["location"]
            controller["contact"] = cont["contact"]
            controller["operState"] = cont["operState"]
            controller["model"] = cont["model"]
            controller["swVersion"] = cont["swVersion"]
            controller["countrySettings"] = cont["countrySettings"]
            controller["mac"] = cont["mac"]

            controller_list.append(controller)

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

        for client in clients:
            client['ap_mac'] = ap_info[client['apId']]
            if find_client(client['mac']):
                update_client_list.append(client)
            else:
                insert_client_list.append(client)

    alarm_mon_data = traverse(alarm_list, alarm_mon_data)

    if len(alarm_mon_data):
        insert_alarm_data(alarm_mon_data)

    if len(update_client_list):
        print "client_update_data\n", update_client_list
        update_client_data(update_client_list)

    if len(insert_client_list):
        print "client_insert_data\n", insert_client_list
        insert_client_data(insert_client_list)

    if len(update_ap_list):
        u_ap_mon_data = traverse(update_ap_list, ap_mon_data)
        update_ap_data(u_ap_mon_data)

    if len(insert_ap_list):
        i_ap_mon_data = traverse(insert_ap_list, ap_mon_data)
        insert_ap_data(i_ap_mon_data)
