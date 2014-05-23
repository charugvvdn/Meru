from pymongo import MongoClient
import datetime
import time
import settings
db = settings.DB
def ap_aggregation(start_time, end_time):
    c = db.device_aps.find({ "timestamp" : { "$gt" : start_time, "$lt" : end_time}})\
        .sort("timestamp", -1)

    for doc in c:
        t_stmp = doc.get('timestamp')
        date_obj = datetime.datetime.utcfromtimestamp(int(t_stmp))
        y, m, d= date_obj.year, date_obj.month, date_obj.day
        h = date_obj.hour
        datetime_obj = datetime.datetime(y, m, d, h)
        print datetime_obj
        c_mac = doc.get('controller_mac').lower()
        ap_mac = doc.get('aps').get('mac')
        ap_status = doc.get('aps').get('status')
        ap_rx = doc.get('aps').get('rxBytes')
        ap_tx = doc.get('aps').get('txBytes')
        ap_info = {"ap_mac" : ap_mac, "ap_status" : ap_status, "ap_rx" : ap_rx, "ap_tx" :\
                     ap_tx,"c_mac" : c_mac}
        c_info = { "c_mac" : c_mac}
        ap_doc = {"hour" : h, "date" : datetime_obj, "timestamp" : t_stmp, "c_info" : \
                    [c_info], "ap_info" : [ap_info]}

        cur = db.ap_date_count.find({"hour" : h, "date" : datetime_obj})
        if cur.count():
            update_cursor = db.ap_date_count.find({"hour" : h, "date" : datetime_obj, \
                            "ap_info.ap_mac" : ap_mac})
            if update_cursor.count():
                db.ap_date_count.update({ "hour" : h, "date" : datetime_obj, "ap_info.ap_mac" : \
                    ap_mac}, {"$set" : {"ap_info.$.ap_tx" : ap_tx, "ap_info.$.ap_rx" : ap_rx,\
                    "ap_info.$.ap_status" : ap_status, "ap_info.$c_mac" : c_mac,\
                    "timestamp" : t_stmp}, "$addToSet" : { "c_info" : c_info}})
            else:
                db.ap_date_count.update({"hour" : h, "date" : datetime_obj}, \
                    { "$addToSet" : { "ap_info" : ap_info, "c_info" : c_info}, "$set" : \
                    { "timestamp" : t_stmp}})
            print "AP doc updated\n"
        else:
            db.ap_date_count.insert(ap_doc)
            print "New AP doc created\n"


def client_aggregation(start_time, end_time):
    c = db.device_clients.find({ "timestamp" : { "$gt" : start_time, "$lt" : end_time}})\
        .sort("timestamp", -1)

    for doc in c:
        t_stmp = doc.get('timestamp')
        date_obj = datetime.datetime.utcfromtimestamp(int(t_stmp))
        y, m, d= date_obj.year, date_obj.month, date_obj.day
        h = date_obj.hour
        datetime_obj = datetime.datetime(y, m, d, h)
        print datetime_obj

        c_mac = doc.get('controller_mac').lower() if doc.get('controller_mac') else doc.get('msolo_mac').lower()
        client_type = doc.get('clients').get('clientType') if doc.get('clients').get('clientType') else 'unknown'
        #client_thru = doc.get('clients').get('rxBytes') + doc.get('clients').get('txBytes')
        client_mac = doc.get('clients').get('mac')
        client_rx = doc.get('clients').get('rxBytes')
        client_tx = doc.get('clients').get('txBytes')
        client_interface = doc.get('clients').get('interface') or 'none'
        client_info = { "client_type" : client_type, "client_rx" : client_rx, "client_tx" : \
                        client_tx, "client_interface":client_interface, "client_mac" : client_mac,"c_mac" : c_mac}
        c_info = { "c_mac" : c_mac}
        client_doc = { "hour" : h, "date" : datetime_obj, "timestamp" : t_stmp, "client_info" : \
                    [client_info], "c_info" : [c_info]}

        cur = db.client_date_count.find({"hour" : h, "date" : datetime_obj})
        if cur.count():
            update_cursor = db.client_date_count.find({"hour" : h, "date" : datetime_obj, \
                            "client_info.client_mac" : client_mac})
            if update_cursor.count():
                db.client_date_count.update({ "hour" : h, "date" : datetime_obj, \
                "client_info.client_mac" : client_mac}, {"$set" : {"client_info.$.client_tx" : \
                client_tx, "client_info.$.client_rx" : client_rx,"client_info.$.c_mac" : c_mac,\
                 "client_info.$.client_interface" : client_interface,\
                 "client_info.$.client_type" : \
                client_type, "timestamp" : t_stmp}, "$addToSet" : { "c_info" : c_info}})
            else:
                db.client_date_count.update({"hour" : h, "date" : datetime_obj}, \
                    { "$addToSet" : { "client_info" : client_info, "c_info" : c_info}, \
                    "$set" : { "timestamp" : t_stmp}})
            print "Client doc updated\n"
        else:
            db.client_date_count.insert(client_doc)
            print "New client doc created\n"

def device_aggregation(start_time, end_time):
    c = db.device_controllers.find({ "timestamp" : { "$gt" : start_time, "$lt" : end_time}})\
        .sort("timestamp", -1)

    for doc in c:
        t_stmp = doc.get('timestamp')
        date_obj = datetime.datetime.utcfromtimestamp(int(t_stmp))
        y, m, d= date_obj.year, date_obj.month, date_obj.day
        h = date_obj.hour
        datetime_obj = datetime.datetime(y, m, d, h)
        print datetime_obj

        c_mac = doc.get('lower_snum').lower()
        device_operState = doc.get('operState') if doc.get('operState') else 'None'
        device_rx = doc.get('rxBytes') or  0
        device_mac = doc.get('lower_snum').lower()
        device_tx = doc.get('txBytes') or 0
        device_info = { "device_operState" : device_operState, "device_rx" : device_rx, "device_tx" : \
                        device_tx, "device_mac" : device_mac,"c_mac" : c_mac}
        c_info = { "c_mac" : c_mac}
        device_doc = { "hour" : h, "date" : datetime_obj, "timestamp" : t_stmp, "device_info" : \
                    [device_info], "c_info" : [c_info]}

        cur = db.device_date_count.find({"hour" : h, "date" : datetime_obj})
        if cur.count():
            update_cursor = db.device_date_count.find({"hour" : h, "date" : datetime_obj, \
                            "device_info.device_mac" : device_mac})
            if update_cursor.count():
                db.device_date_count.update({ "hour" : h, "date" : datetime_obj, \
                "device_info.device_mac" : device_mac}, {"$set" : {"device_info.$.device_tx" : \
                device_tx, "device.$.device_rx" : device_rx, "device.$.c_mac" : c_mac,\
                "device.$.operState" : device_operState,\
                 "device_info.$.device_type" : device_type, "timestamp" : t_stmp}, \
                 "$addToSet" : { "c_info" : c_info}})
            else:
                db.device_date_count.update({"hour" : h, "date" : datetime_obj}, \
                    { "$addToSet" : { "device_info" : device_info, "c_info" : c_info}, \
                    "$set" : { "timestamp" : t_stmp}})
            print "device doc updated\n"
        else:
            db.device_date_count.insert(device_doc)
            print "New device doc created\n"

def msolo_radioparam_aggregation(start_time, end_time):
    c = db.device_radio_params.find({ "timestamp" : { "$gt" : start_time, "$lt" : end_time}})\
        .sort("timestamp", -1)

    for doc in c:
        t_stmp = doc.get('timestamp')
        date_obj = datetime.datetime.utcfromtimestamp(int(t_stmp))
        y, m, d= date_obj.year, date_obj.month, date_obj.day
        h = date_obj.hour
        datetime_obj = datetime.datetime(y, m, d, h)
        print datetime_obj

        msolo_mac = doc.get('msolo_mac').lower()
        #client_thru = doc.get('clients').get('rxBytes') + doc.get('clients').get('txBytes')
        radio_mac = doc.get('radio_params').get('mac')
        radio_rx = doc.get('radio_params').get('rx-bytes')
        radio_tx = doc.get('radio_params').get('tx-bytes')
        radio_interface = doc.get('radio_params').get('interface')
        radio_status = doc.get('radio_params').get('status')

        radio_info = { "radio_rx" : radio_rx, "radio_tx" : \
                        radio_tx, "radio_interface":radio_interface,\
                        "radio_interface": radio_interface , \
                        "radio_status" : radio_status, "radio_mac" : radio_mac}
        msolo_info = { "msolo_mac" : msolo_mac}
        radio_doc = { "hour" : h, "date" : datetime_obj, "timestamp" : t_stmp, "radio_info" : \
                    [radio_info], "msolo_info" : [msolo_info]}

        cur = db.msolo_radio_date_count.find({"hour" : h, "date" : datetime_obj})
        if cur.count():
            update_cursor = db.msolo_radio_date_count.find({"hour" : h, "date" : datetime_obj, \
                            "radio_info.radio_mac" : radio_mac})
            if update_cursor.count():
                db.msolo_radio_date_count.update({ "hour" : h, "date" : datetime_obj, \
                "radio_info.radio_mac" : radio_mac}, {"$set" : {"radio_info.$.radio_tx" : \
                radio_tx, "radio_info.$.radio_rx" : radio_rx, "radio_info.$.radio_interface" : \
                radio_interface, "radio_info.$.radio_status" : radio_status, \
                 "timestamp" : t_stmp}, "$addToSet" : { "msolo_info" : msolo_info}})
            else:
                db.msolo_radio_date_count.update({"hour" : h, "date" : datetime_obj}, \
                    { "$addToSet" : { "radio_info" : radio_info, "msolo_info" : msolo_info}, \
                    "$set" : { "timestamp" : t_stmp}})
            print "mSolo radio doc updated\n"
        else:
            db.msolo_radio_date_count.insert(radio_doc)
            print "New mSolo radio doc created\n"

def main():
    
    offset  = datetime.datetime.utcnow() - datetime.timedelta(minutes=1)
    start_time = int((offset - datetime.datetime(1970, 1, 1)).total_seconds())
    end_time  = int((datetime.datetime.utcnow() - datetime.datetime(1970, 1, 1)).\
                total_seconds())

    ap_aggregation(start_time, end_time)
    client_aggregation(start_time, end_time)
    device_aggregation(start_time, end_time)
    msolo_radioparam_aggregation(start_time, end_time)


if __name__ == "__main__":
    main()
