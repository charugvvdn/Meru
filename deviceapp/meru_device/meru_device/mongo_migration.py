from pymongo import MongoClient
import datetime
import time

def ap_aggregation(start_time, end_time):
    c = db.device_aps.find({ "timestamp" : { "$gt" : start_time, "$lt" : end_time}})\
        .sort("timestamp", -1)

    for doc in c:
        t_stmp = doc.get('timestamp')
        date_obj = datetime.datetime.fromtimestamp(int(t_stmp))
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
                     ap_tx}
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
                    "ap_info.$.ap_status" : ap_status, "timestamp" : t_stmp}, "$addToSet" : \
                    { "c_info" : c_info}})
            else:
                db.ap_date_count.update({"hour" : h, "date" : datetime_obj}, \
                    { "$addToSet" : { "ap_info" : ap_info, "c_info" : c_info}, "$set" : \
                    { "timestamp" : t_stmp}})
            print "AP doc updated\n"
        else:
            db.ap_date_count.insert(ap_doc)
            print "New AP doc created\n"


def client_aggregation(start_time, end_time):
    c = db.device_clients.find({ "controller_mac":{'$exists': 1}, "timestamp" : { "$gt" : start_time, "$lt" : end_time}})\
        .sort("timestamp", -1)

    for doc in c:
        t_stmp = doc.get('timestamp')
        date_obj = datetime.datetime.fromtimestamp(int(t_stmp))
        y, m, d= date_obj.year, date_obj.month, date_obj.day
        h = date_obj.hour
        datetime_obj = datetime.datetime(y, m, d, h)
        print datetime_obj

        c_mac = doc.get('controller_mac').lower()
        client_type = doc.get('clients').get('clientType')
        #client_thru = doc.get('clients').get('rxBytes') + doc.get('clients').get('txBytes')
        client_mac = doc.get('clients').get('mac')
        client_rx = doc.get('clients').get('rxBytes')
        client_tx = doc.get('clients').get('txBytes')
        client_info = { "client_type" : client_type, "client_rx" : client_rx, "client_tx" : \
                        client_tx, "client_mac" : client_mac}
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
                client_tx, "client_info.$.client_rx" : client_rx, "client_info.$.client_type" : \
                client_type, "timestamp" : t_stmp}, "$addToSet" : { "c_info" : c_info}})
            else:
                db.client_date_count.update({"hour" : h, "date" : datetime_obj}, \
                    { "$addToSet" : { "client_info" : client_info, "c_info" : c_info}, \
                    "$set" : { "timestamp" : t_stmp}})
            print "Client doc updated\n"
        else:
            db.client_date_count.insert(client_doc)
            print "New client doc created\n"


def main():
    global db
    db = MongoClient()['nms']

    offset  = datetime.datetime.utcnow() - datetime.timedelta(minutes=1)
    start_time = int((offset - datetime.datetime(1970, 1, 1)).total_seconds())
    end_time  = int((datetime.datetime.utcnow() - datetime.datetime(1970, 1, 1)).\
                total_seconds())

    ap_aggregation(start_time, end_time)
    client_aggregation(start_time, end_time)

if __name__ == "__main__":
    main()
