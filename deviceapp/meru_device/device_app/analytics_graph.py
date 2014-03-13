from pymongo import MongoClient
from django.http import HttpResponse
import datetime
import json
from django.views.generic.base import View
import ast
import csv, json
# Connection with mongoDB client
CLIENT = MongoClient()
DB = CLIENT['nms']
utc_1970 = datetime.datetime(1970, 1, 1) #UTC since jan 1970
utc_now = datetime.datetime.utcnow() #UTC now


class AnalyticsReport():

    '''Common variable used under the class methods'''
    def __init__(self,**kwargs):
        self.lt= kwargs['lt']
        self.gt = kwargs['gt']
        #self.mac = kwargs['mac']
        self.doc_list = []
        self.get_data = {}
        if self.lt and self.gt and self.mac:
            self.cursor = DB.devices.find({ "lower_snum":{self.mac.lower()}, "timestamp": {"$gt": self.gt, "$lt": self.lt}}).sort('timestamp', -1)
        elif self.lt and self.gt:
            self.cursor = DB.devices.find({ "timestamp": {"$gt": self.gt, "$lt": self.lt}}).\
                                sort('timestamp', -1)
            for doc in self.cursor:
                self.doc_list.append(doc)
     def clientDeviceType(self, **kwargs ):

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
    def busiestClients(self, **kwargs ):
        '''Calculating top 5 busiest clients '''
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
            if len(result_list) < 5:
                csv_data = {}
                result_list.append([client_mac,unique_clients[client_mac]])
                csv_data[client_mac] = unique_clients[client_mac]
                csv_result_list.append(csv_data)

        
        print result_list
        #gen_csv('Busiest Client','Clients count',json.dumps(csv_result_list))
        return result_list
    def report_analytics (self,**kwargs):
        # to count the number of online aps for last 24 hours
        typeof = 'clients'
        result_list = []
        doc_list = []
        # create a dictionary for 24 hours
        date_dict ={}
        
        from_time = self.gt
        to_time = self.lt
        
        while from_time <= to_time:
            thistime = datetime.datetime.utcfromtimestamp(from_time)
            thisdate = str(thistime.date())
            
            if thisdate not in date_dict:
                date_dict[thisdate] = {"no_of_client":{},"onlineAPs":{},"controller_thru":{}}
                if thistime.time().hour not in date_dict[thisdate]['no_of_client']:
                    date_dict[thisdate]['no_of_client'][thistime.time().hour] = 0
                if thistime.time().hour not in date_dict[thisdate]['onlineAPs']:
                    date_dict[thisdate]['onlineAPs'][thistime.time().hour] = 0
                if thistime.time().hour not in date_dict[thisdate]['controller_thru']:
                    date_dict[thisdate]['controller_thru'][thistime.time().hour] = 0
            else:
                if thistime.time().hour not in date_dict[thisdate]['no_of_client']:
                    date_dict[thisdate]['no_of_client'][thistime.time().hour] = 0
                if thistime.time().hour not in date_dict[thisdate]['onlineAPs']:
                    date_dict[thisdate]['onlineAPs'][thistime.time().hour] = 0
                if thistime.time().hour not in date_dict[thisdate]['controller_thru']:
                    date_dict[thisdate]['controller_thru'][thistime.time().hour] = 0
            from_time = from_time + 1 * 60 * 60
        
        
        '''counting 
        1. no of clients
        2. online aps
        3. controller throughput 
            from documents filetered on timestamp'''
        
        for doc in self.doc_list:
            client_rx = 0
            client_tx = 0
            ap_rx = 0
            ap_tx = 0
            current_time = datetime.datetime.utcfromtimestamp(doc['timestamp'])
            currentdate = str(current_time.date())
            if currentdate in date_dict:
                if 'msgBody' in doc and 'controller' in doc['msgBody']:
                    if typeof in doc['msgBody'].get('controller'):
                        if current_time.time().hour in date_dict[currentdate]['no_of_client']:
                            clients = doc.get('msgBody').get('controller').get('clients')
                            date_dict[currentdate]['no_of_client'][current_time.time().hour] += len(clients)
                            for client in clients:
                                client_rx += client['rxBytes']
                                client_tx += client['txBytes']
                        if current_time.time().hour in date_dict[currentdate]['onlineAPs']:
                            aps = doc.get('msgBody').get('controller').get('aps')
                            for ap in aps:
                                if ap['status'].lower() == 'up':
                                    date_dict[currentdate]['onlineAPs'][current_time.time().hour] += 1
                                    ap_rx += ap['rxBytes']
                                    ap_tx += ap['txBytes']
                        if current_time.time().hour in date_dict[currentdate]['controller_thru']:
                            date_dict[currentdate]['controller_thru'][current_time.time().hour] += (client_rx+ap_rx) +(client_tx+ap_tx)

        return date_dict

class analytics_api(View):

    
    def get(self, request):
        
        ''' API calls initaited for analtics graph page'''
        response_list = []
        request_dict ={}
        response = {}
        
        for key in request.GET:
            request_dict = {}
            request_dict[key] = ast.literal_eval(request.GET.get(key).strip()
                                 ) if request.GET.get(key) else 0
        if 'time' in request_dict:
            if request_dict['time'][0] > request_dict['time'][1]:
                response = HttpResponse(json.dumps({"status": "false","message": "Wrong time range"}))
            if not response:
                obj = AnalyticsReport(gt=request_dict['time'][0],lt=request_dict['time'][1])
                response_list.append(obj.report_analytics())
                response = HttpResponse(json.dumps({"status": "true","values":response_list,"message": "onlineAPs, no.of clients and controller thoughput"}))
        else:
            response = HttpResponse(json.dumps({"status": "false","message": "No time stamp specified"}))
        return response
