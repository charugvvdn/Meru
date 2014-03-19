from pymongo import MongoClient
from django.http import HttpResponse
import datetime
import json
from django.views.generic.base import View
import ast
import csv, json
import random
from random import randint
# Connection with mongoDB client
CLIENT = MongoClient()
DB = CLIENT['nms']
utc_1970 = datetime.datetime(1970, 1, 1) #UTC since jan 1970
utc_now = datetime.datetime.utcnow() #UTC now


class AnalyticsReport():

    '''Common variable used under the class methods'''
    def __init__(self,**kwargs):
        self.lt= kwargs['lt'] if 'lt' in kwargs else None
        self.gt = kwargs['gt'] if 'gt' in kwargs else None
        self.maclist = kwargs['maclist'] if 'maclist' in kwargs else None
        self.doc_list = []
        self.get_data = {}
        
        if self.lt and self.gt and self.maclist:
            for mac in self.maclist:
                self.cursor = DB.devices.find({ "lower_snum":mac.lower(), "timestamp": {"$gt": self.gt, "$lt": self.lt}}).sort('timestamp', -1)
                for doc in self.cursor:
                    self.doc_list.append(doc)
        elif self.lt and self.gt:
            self.cursor = DB.devices.find({ "timestamp": {"$gt": self.gt, "$lt": self.lt}}).\
                                sort('timestamp', -1)
            for doc in self.cursor:
                self.doc_list.append(doc)
        
    def clientDeviceType(self, **kwargs ):

        '''Calculating device type of clients '''
        typeof = 'clients'
        device_dict = {"device_type":{"mac":0,"iphone":0,"ubuntu":0,"windows":0,"android":0}}
        unique_clients = {}
        
        for doc in self.doc_list:
            if 'msgBody' in doc and 'controller' in doc['msgBody']:
                if typeof in doc['msgBody'].get('controller'):
                    # get clients
                    
                    clients = doc.get('msgBody').get('controller').get(typeof)
                    for client in clients:
                        if client["mac"] not in unique_clients:
                            if client['clientType'].lower() in device_dict['device_type']:
                                device_dict['device_type'][client['clientType'].lower()] += 1
                            
                            unique_clients[client["mac"]] = 0
                    
        
        return device_dict

    def busiestClients(self, **kwargs ):
        '''Calculating top 5 busiest clients '''
        typeof = 'clients'
        busiest_dict = {"busiest_client":[]}
        result_list = []
        temp_dict = {}
        unique_clients = {}
        
        for doc in self.doc_list:
            if 'msgBody' in doc and 'controller' in doc['msgBody']:
                if typeof in doc['msgBody'].get('controller'):
                    # get clients
                    clients = doc.get('msgBody').get('controller').get(typeof)
                    for client in clients:
                        #if len(unique_clients['busiest_client']) < 5:
                        if client["mac"] not in unique_clients:
                            usage = client['rxBytes']+client['txBytes']
                            unique_clients[client["mac"]] = usage
                            
                        else:
                            if client['rxBytes']+client['txBytes'] > unique_clients[client['mac']]:
                                usage = client['rxBytes']+client['txBytes']
                                unique_clients[client['mac']] = usage
        temp_dict = sorted(unique_clients.values(),reverse=True)[:5] if len(unique_clients)>5 else unique_clients
        for mac in temp_dict:
            result_dict = {}
            result_dict['mac']= mac
            result_dict['usage'] =  temp_dict[mac]
            busiest_dict['busiest_client'].append(result_dict)
        return busiest_dict

    def report_analytics (self,**kwargs):
        # to count the number of online aps for last 24 hours
        typeof = 'clients'
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
                            date_dict[currentdate]['controller_thru'][current_time.time().hour] += randint(20000,100000)#(client_rx+ap_rx) +(client_tx+ap_tx)

        return date_dict

class analytics_api(View):

    
    def get(self, request):
        
        ''' API calls initaited for analtics graph page'''
        response_list = []
        request_dict ={}
        response = {}
        maclist = []
        for key in request.GET:

            request_dict[key] = ast.literal_eval(request.GET.get(key).strip()
                                 ) if request.GET.get(key) else 0
        if "time" not in request_dict:
                response = HttpResponse(json.dumps({"status": "false","message": "No time stamp specified"}))
        if not response and request_dict['time'][0] > request_dict['time'][1]:
                response = HttpResponse(json.dumps({"status": "false","message": "Wrong time range"}))
        if not response:
            if 'time' in request_dict and "mac" in request_dict:
                # API for gathering detailed info about the analyitics point graph on timestamp and MAC list basis
                maclist = request_dict['mac']
                obj = AnalyticsReport(maclist = maclist, gt=request_dict['time'][0],lt=request_dict['time'][1])
                response_list.append(obj.busiestClients())
                response_list.append(obj.clientDeviceType())
                response = HttpResponse(json.dumps({"status": "true","values":response_list,"message": "Device type distribution and 5 busiest clients"}))
            
            elif 'time' in request_dict:
                # API for gathering info about the analyitics point graph on the basis of timestamp
                obj = AnalyticsReport(gt=request_dict['time'][0],lt=request_dict['time'][1])
                response_list.append(obj.report_analytics())
                response = HttpResponse(json.dumps({"status": "true","values":response_list,"message": "onlineAPs, no.of clients and controller thoughput"}))
            
        return response
