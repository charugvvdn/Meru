from pymongo import MongoClient
from django.http import HttpResponse
import datetime
import json
import ast
import csv, json
# Connection with mongoDB client
CLIENT = MongoClient()
DB = CLIENT['nms']
utc_1970 = datetime.datetime(1970, 1, 1) #UTC since jan 1970
utc_now = datetime.datetime.utcnow() #UTC now
def gen_csv(col1,col2,x):
    x = json.loads(x)
    f = csv.writer(open("/home/charu/csv_reports/"+col1+".csv", "wb+"))
    f.writerow([col1, col2])
    for row in x:
        f.writerow( [row.keys()[0],row.values()[0]])

class ClientReport():

    '''Common variable used under the class methods'''
    def __init__(self,**kwargs):
        self.lt= kwargs['lt']
        self.gt = kwargs['gt']
        self.mac = kwargs['mac']
        self.doc_list = []
        for mac in self.mac:
            self.cursor = DB.devices.find({ "timestamp": {"$gt": self.gt, "$lt": self.lt}}).\
                                sort('timestamp', -1)
            for doc in self.cursor:
                self.doc_list.append(doc)

    def busiestClients(self, **kwargs ):
        '''Calculating top 10 busiest clients '''
        typeof = 'clients'
        result_list = []
        usage = 0
        
        doc_list = []
        csv_result_list = []
        unique_clients = {}
        for doc in self.doc_list:
            if 'msgBody' in doc and 'controller' in doc['msgBody']:
                if typeof in doc['msgBody'].get('controller'):
                    # get clients
                    
                    clients = doc.get('msgBody').get('controller').get(typeof)
                    for client in clients:
                        if client["mac"] not in unique_clients:
                            usage = client['rxBytes']+client['txBytes']
                            unique_clients[client["mac"]] = usage
                            
                        else:
                            if client['rxBytes']+client['txBytes'] > unique_clients[client['mac']]:
                                usage = client['rxBytes']+client['txBytes']
                                unique_clients[client['mac']] = usage
        for client_mac in unique_clients:
            if len(result_list) < 10:
                csv_data = {}
                result_list.append([client_mac,unique_clients[client_mac]])
                csv_data[client_mac] = unique_clients[client_mac]
                csv_result_list.append(csv_data)

        
        print result_list
        #gen_csv('Busiest Client','Clients count',json.dumps(csv_result_list))
        return result_list
    def summaryClient(self, **kwargs ):

        '''Calculating device type of clients '''
        typeof = 'clients'
        result_list = []
        doc_list = []
        csv_result_list = []
        device_dict = {}
        unique_clients = {}
        for doc in self.doc_list:
            if 'msgBody' in doc and 'controller' in doc['msgBody']:
                if typeof in doc['msgBody'].get('controller'):
                    # get clients
                    
                    clients = doc.get('msgBody').get('controller').get(typeof)
                    for client in clients:
                        if client["mac"] not in unique_clients:
                            if client['clientType'] in device_dict:
                                device_dict[client['clientType']] += 1
                            else:
                                device_dict[client['clientType']] = 1

                            unique_clients[client["mac"]] = 0
                    
        for device in device_dict:
            result_list.append([device,device_dict[device]])
            csv_data = {}
            csv_data[device]=device_dict[device]
            csv_result_list.append(csv_data)
        print result_list
        #gen_csv('Device Type','Device count',json.dumps(csv_result_list))
        return result_list
    def uniqueClient(self, **kwargs ):
        '''Calculating unique clients '''
        typeof = 'clients'
        result_list = []
        perday_dict = {}
        csv_result_list = []
        unique_clients = {}
        for doc in self.doc_list:
            if 'msgBody' in doc and 'controller' in doc['msgBody']:
                if typeof in doc['msgBody'].get('controller'):
                    # get clients
                    thisdate = datetime.datetime.utcfromtimestamp(doc['timestamp'])
                    clients = doc.get('msgBody').get('controller').get(typeof)
                    for client in clients:
                        if client["mac"] not in unique_clients:
                            unique_clients[client["mac"]] = 0
                            if thisdate.date() not in perday_dict:
                                perday_dict[thisdate.date()] = [client["mac"]]
                            else:
                                perday_dict[thisdate.date()].append(client["mac"])
        for perday in perday_dict:
            result_list.append([perday,perday_dict[perday]])
            csv_data = {}
            csv_data[str(perday)]=perday_dict[perday]
            csv_result_list.append(csv_data)

        print result_list
        #gen_csv('Unique clients','Clients count',json.dumps(csv_result_list))
        return result_list
    def maxClient(self, **kwargs ):
        '''Calculating unique clients '''
        typeof = 'clients'
        result_list = []
        perday_dict = {}
        csv_result_list = []
        unique_clients = {}
        for doc in self.doc_list:
            if 'msgBody' in doc and 'controller' in doc['msgBody']:
                if typeof in doc['msgBody'].get('controller'):
                    # get clients
                    thisdate = datetime.datetime.utcfromtimestamp(doc['timestamp'])
                    clients = doc.get('msgBody').get('controller').get(typeof)
                    for client in clients:
                        if client["mac"] not in unique_clients:
                            unique_clients[client["mac"]] = 0
                            if thisdate.date() not in perday_dict:
                                perday_dict[thisdate.date()] = 1
                            else:
                                perday_dict[thisdate.date()] += 1
        for perday in perday_dict:
            result_list.append([perday,perday_dict[perday]])
            csv_data = {}
            csv_data[str(perday)]=perday_dict[perday]
            csv_result_list.append(csv_data)

        print result_list
        #gen_csv('Max clients','Clients count',json.dumps(csv_result_list))
        return result_list

    def ssidClient(self, **kwargs ):
        '''Calculating clients by SSID '''
        typeof = 'clients'
        result_list = []
        doc_list = []
        csv_result_list = []
        ssid_dict = {}
        unique_clients = {}
        for doc in self.doc_list:
            if 'msgBody' in doc and 'controller' in doc['msgBody']:
                if typeof in doc['msgBody'].get('controller'):
                    # get clients
                    
                    clients = doc.get('msgBody').get('controller').get(typeof)
                    for client in clients:
                        if client["mac"] not in unique_clients:
                            if client['ssid'] not in ssid_dict:
                                ssid_dict[client['ssid']] = 1
                            else:
                                ssid_dict[client['ssid']] += 1
                            unique_clients[client["mac"]] = 0
        for ssid in ssid_dict:
            result_list.append([ssid,ssid_dict[ssid]])
            csv_data = {} 
            csv_data[ssid] = ssid_dict[ssid]
            csv_result_list.append(csv_data)
        print result_list
        #gen_csv('SSID','Clients count',json.dumps(csv_result_list))
        return result_list
def main():
    
    obj = ClientReport(mac=['aa:bb:cc:dd:174:dd','AA:BB:CC:DD:43:DD'],gt=1394417641,lt=1394627625)
    '''ts = 1392636637
    print datetime.datetime.utcfromtimestamp(ts)
    print datetime.datetime.utcnow()
    print datetime.datetime.utcnow()-datetime.datetime.utcfromtimestamp(ts)
    eachday = utc_now- datetime.timedelta(days=1) #UTC for last day
    print int((eachday - utc_1970).total_seconds()) #converting to last day timestamp'''
    
    obj.busiestClients()
    obj.summaryClient()
    obj.uniqueClient()
    obj.maxClient()
    obj.ssidClient()
    #obj.report_analytics ()

    '''response_list = []
    response_list.append(obj.report_analytics ())
    print response_list
    response = HttpResponse(json.dumps({"status": "true", "data": response_list }))
    return response'''
if __name__ == "__main__":
        main()

