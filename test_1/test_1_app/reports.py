from pymongo import MongoClient
import datetime
import json
import ast

# Connection with mongoDB client
CLIENT = MongoClient()
DB = CLIENT['nms']
UTC_1970 = datetime.datetime(1970, 1, 1)
UTC_NOW = datetime.datetime.utcnow()
OFFSET = UTC_NOW - datetime.timedelta(minutes=30)
class ClientReport():

    '''Common variable used under the class methods'''
    def __init__(self,**kwargs):
        self.lt= kwargs['lt']
        self.gt = kwargs['gt']
        self.doc_list = []
        self.cursor = DB.devices.find({"timestamp" : {"$gt":self.lt , "$lt":self.gt }})
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
                                unique_client[client['mac']] = usage
        for client_mac in unique_clients:
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
        doc_list = []
        unique_clients = {}
        for doc in self.doc_list:
            if 'msgBody' in doc and 'controller' in doc['msgBody']:
                if typeof in doc['msgBody'].get('controller'):
                    # get clients
                    
                    clients = doc.get('msgBody').get('controller').get(typeof)
                    for client in clients:
                        if client["mac"] not in unique_clients:
                            unique_clients[client["mac"]] = 0
                            result_list.append(client["mac"])
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
                                ssid_dict[client['ssid']] = 0
                            else:
                                ssid_dict[client['ssid']] += 1
                            unique_clients[client["mac"]] = 0
        for ssid in ssid_dict:
            result_list.append([ssid,ssid_dict[ssid]])
        print result_list
        return result_list
def main():
    obj = ClientReport(lt=1392636637,gt=1392871845)
    obj.busiestClients()
    obj.summaryClient()
    obj.uniqueClient()
    obj.ssidClient()

if __name__ == "__main__":
        main()

