from pymongo import MongoClient
import datetime
import time
import settings

db = settings.DB
def ap_quantification(start_time, end_time):
    c = db.device_aps.find({ "timestamp" : { "$gt" : start_time, "$lt" : end_time}})\
        .sort("_id", -1)
    unique_aps = []

    for doc in c:
        if doc.get('aps').get('mac') not in unique_aps:
            lower_snum = doc.get('lower_snum')
            timestamp = doc.get('timestamp')
            ap_mac = doc.get('aps').get('mac')
            unique_aps.append(ap_mac)
            status = doc.get('aps').get('status')
            rx = doc.get('aps').get('rxBytes')
            tx = doc.get('aps').get('txBytes')
            wifi = doc.get('aps').get('wifiExp')
            ap_id = doc.get('aps').get('id')
            model = doc.get('aps').get('model')
            ap_docs = db.ap_stats.find({ "ap_mac" : ap_mac}).count()
            if ap_docs:
                db.ap_stats.update({ "ap_mac" : ap_mac}, { "$set" : { "lower_snum" : lower_snum,\
                    "status" : status, "txBytes" : tx, "rxBytes" : rx, "wifiExp" : wifi,\
                    "id" : ap_id, "model" : model, "timestamp" : timestamp}})
                print "Ap doc updated - Mac : " + str(ap_mac)
            else:
                db.ap_stats.insert({ "lower_snum" : lower_snum, "ap_mac" : ap_mac, "status" : status,\
                    "txBytes" : tx, "rxBytes" : rx, "wifiExp" : wifi, "id" : ap_id, "model" : model, "timestamp" : timestamp})
                print "Ap doc inserted - Mac : " + str(ap_mac)

def client_quantification(start_time, end_time):
    c = db.device_clients.find({ "timestamp" : { "$gt" : start_time, "$lt" : end_time}})\
        .sort("_id", -1)
    unique_clients = []

    for doc in c:
        client_state = ''
        if doc.get('clients').get('mac') not in unique_clients:
            lower_snum = doc.get('lower_snum')
            timestamp = doc.get('timestamp')
            ap_mac = doc.get('ap_mac') if doc.get('ap_mac') else lower_snum
            client_mac = doc.get('clients').get('mac')
            unique_clients.append(client_mac)
            if doc.get('clients').get('state'):
                client_state = doc.get('clients').get('state')
            elif doc.get('clients').get('associated'):
                if doc.get('clients').get('associated') == 'yes':
                    client_state = 'associated'
                else:
                    client_state = 'not associated'
            state = client_state
            rx = doc.get('clients').get('rxBytes')
            tx = doc.get('clients').get('txBytes')
            ap_id = doc.get('clients').get('apId') if doc.get('clients').get('apId') else 0
            client_docs = db.client_stats.find({ "client_mac" : client_mac}).count()
            if client_docs:
                db.client_stats.update({ "client_mac" : client_mac}, { "$set" : {\
                    "lower_snum" : lower_snum, "state" : state, "txBytes" : tx,\
                    "rxBytes" : rx, "ap_id" : ap_id, "ap_mac" : ap_mac, "timestamp" : timestamp}})
                print "Client doc updated - Mac : " + str(client_mac)
            else:
                db.client_stats.insert({ "lower_snum" : lower_snum, "ap_mac" : ap_mac,\
                    "client_mac" : client_mac, "state" : state, "rxBytes" : rx,\
                    "txBytes" : tx, "ap_id" : ap_id, "timestamp" : timestamp})
                print "Client doc inserted - Mac : " + str(client_mac)


def main():
    
    
    
    offset  = datetime.datetime.utcnow() - datetime.timedelta(minutes=1)
    start_time = int((offset - datetime.datetime(1970, 1, 1)).total_seconds())
    end_time  = int((datetime.datetime.utcnow() - datetime.datetime(1970, 1, 1)).\
                total_seconds())
    client_quantification(start_time, end_time)
    ap_quantification(start_time, end_time)
    

if __name__ == "__main__":
    print "\n" + "Exec Time :: " + str(datetime.datetime.now()) + "\n"
    main()
