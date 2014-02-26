from pymongo import MongoClient
import datetime
import json
import ast
# Connection with mongoDB client
CLIENT = MongoClient()
DB = CLIENT['nms']
utc_1970 = datetime.datetime(1970, 1, 1) #UTC since jan 1970
utc_now = datetime.datetime.utcnow() #UTC now
class ClientReport():

    '''Common variable used under the class methods'''
    def __init__(self,**kwargs):
        self.lt= kwargs['lt']
        self.gt = kwargs['gt']
        self.doc_list = []
        self.cursor = DB.devices.find({"timestamp" : {"$gt":self.gt , "$lt":self.lt }})
        for doc in self.cursor:
            self.doc_list.append(doc)
    def busiestClients(self, **kwargs ):
        '''Calculating top 10 busiest clients '''
        typeof = 'clients'
        result_list = []
        usage = 0
        doc_list = []
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
                result_list.append([client_mac,unique_clients[client_mac]])

        print result_list
        return result_list
    def summaryClient(self, **kwargs ):

        '''Calculating device type of clients '''
        typeof = 'clients'
        result_list = []
        doc_list = []
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
        print result_list
        return result_list
    def uniqueClient(self, **kwargs ):
        '''Calculating unique clients '''
        typeof = 'clients'
        result_list = []
        perday_dict = {}
        unique_clients = {}
        for doc in self.doc_list:
            if 'msgBody' in doc and 'controller' in doc['msgBody']:
                if typeof in doc['msgBody'].get('controller'):
                    # get clients
                    thisdate = datetime.datetime.utcfromtimestamp(doc['timestamp'])
                    previousdate = thisdate-datetime.timedelta(days=1)
                    previousdate_timestamp = int((previousdate - utc_1970).total_seconds())
                    clients = doc.get('msgBody').get('controller').get(typeof)
                    for client in clients:
                        if client["mac"] not in unique_clients:
                            unique_clients[client["mac"]] = 0
                            if previousdate.date() not in perday_dict:
                                perday_dict[previousdate.date()] = 1
                            else:
                                perday_dict[previousdate.date()] += 1
        for perday in perday_dict:
            result_list.append([perday,perday_dict[perday]])
        print result_list
        return result_list
    def ssidClient(self, **kwargs ):
        '''Calculating clients by SSID '''
        typeof = 'clients'
        result_list = []
        doc_list = []
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
        print result_list
        return result_list
def main():
    
    obj = ClientReport(gt=1393390192,lt=1393390200)
    '''ts = 1392636637
    print datetime.datetime.utcfromtimestamp(ts)
    print datetime.datetime.utcnow()
    print datetime.datetime.utcnow()-datetime.datetime.utcfromtimestamp(ts)
    eachday = utc_now- datetime.timedelta(days=1) #UTC for last day
    print int((eachday - utc_1970).total_seconds()) #converting to last day timestamp'''
    obj.busiestClients()
    obj.summaryClient()
    obj.uniqueClient()
    obj.ssidClient()

if __name__ == "__main__":
        main()

