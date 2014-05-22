from pymongo import MongoClient
from django.http import HttpResponse
import datetime
import json
from django.views.generic.base import View
import ast
import csv, json
import random
from collections import Counter
from operator import itemgetter
from random import randint
from meru_device import settings
# Connection with mongoDB client

DB = settings.DB

utc_1970 = datetime.datetime(1970, 1, 1) #UTC since jan 1970
utc_now = datetime.datetime.utcnow() #UTC now


class Hourly_Graph():

    '''Common variable used under the class methods'''
    def __init__(self,**kwargs):
	print "Memory Report"
	memory_report = self.memory_usage()
	print memory_report
        self.lt= kwargs['lt'] if 'lt' in kwargs else None
        self.gt = kwargs['gt'] if 'gt' in kwargs else None
        self.type = kwargs['type'] if 'type' in kwargs else None
        self.maclist = kwargs['maclist'] if 'maclist' in kwargs else None
        self.radio_doc_list = []
        self.client_doc_list = []
        qry = {}
        self.maclist = map(str.lower, self.maclist)
        if self.lt and self.gt and self.maclist:
            lt = datetime.datetime.utcfromtimestamp(self.lt)
            gt = datetime.datetime.utcfromtimestamp(self.gt)
            
            #for mac in self.maclist:
            self.maclist = map(str.lower,self.maclist)
            qry["date"] =  {"$gte": gt, "$lte": lt}
            qry['msolo_info.msolo_mac'] = { "$in": self.maclist}
            print qry
            self.cl_cursor = DB.client_date_count.find({"date":{"$gte":gt,"$lte":lt},"c_info.c_mac":{"$in":self.maclist}}).sort('_id',-1)
            self.rd_cursor = DB.msolo_radio_date_count.find(qry).sort('_id',-1)
            for doc in self.cl_cursor:
                self.client_doc_list.append(doc)
            for doc in self.rd_cursor:
                self.radio_doc_list.append(doc)   
      
    def report_analytics (self,**kwargs):
        # to count the number of online aps for last 24 hours
        date_dict ={}
        date_dict=self.time_grouping()
        to = self.gt
        frm = self.gt
        add_time = 0
        loop_over = 0
        if date_dict['month'] > 0:
                loop_over = date_dict['month']
                add_time = 30*24
        elif date_dict['week'] > 0:
                loop_over = date_dict['week']
                add_time = 7*24
        elif date_dict['days'] > 0:
                loop_over = date_dict['days']
                add_time= 24
        elif date_dict['hours'] > 0:
                loop_over = date_dict['hours']
                add_time= 1
        return loop_over,add_time
    def memory_usage(self):
        """Memory usage of the current process in kilobytes."""
        status = None
        result = {'peak': 0, 'rss': 0}
        try:
            status = open('/proc/self/status')
            for line in status:
                parts = line.split()
                key = parts[0][2:-1].lower()
                if key in result:
                    result[key] = int(parts[1])
        finally:
            if status is not None:
                status.close()
        return result
    

    def thruBand(self, **kwargs):

        '''Calculating the  number of radio params having 
        band as 2.4 Ghz and 5 Ghz for each hour'''
        thruBand = []
        band = '2.4Ghz'
        band1_tmpdict = {}
        loop_over,add_time = self.report_analytics()
        for doc in self.radio_doc_list:
            radios = doc.get('radio_info')
            throughput = 0
            for radio in radios:
                # separate calculation for grouping band on hours
                if radio['radio_interface'] == 'wlan0':
                    band = '2.4Ghz'
                elif radio['radio_interface'] == 'wlan1':
                    band = '5Ghz'
                if band not in band1_tmpdict:
                    band1_tmpdict[band] = {}
                if doc['hour'] not in band1_tmpdict[band]:
                    band1_tmpdict[band][doc['hour']] = {}
                if radio['radio_mac'] not in band1_tmpdict[band][doc['hour']]:
                    band1_tmpdict[band][doc['hour']][radio['radio_mac']] = 0
                throughput = radio['radio_rx']+radio['radio_tx']
                band1_tmpdict[band][doc['hour']][radio['radio_mac']] += throughput
                
        print band1_tmpdict
        for band in band1_tmpdict:
            result_band1 = {}
            result_band1['band'] = band 
            result_band1['values'] = {count:0 for count in range(0,loop_over)}
            for hour in band1_tmpdict[band]:
                if hour in result_band1['values']:
                    for mac in band1_tmpdict[band][hour]:
                        result_band1['values'][hour] += band1_tmpdict[band][hour][mac] 
        
            thruBand.append(result_band1)
        
        return thruBand

    def clientBand(self, **kwargs): 
        '''Calculating the  number of clients having 
        band as 2.4 ghz and 5 Ghz for each hour'''

        clientBand = []
        band = '2.4Ghz'
        band1_tmpdict = {"2.4Ghz":{},"5Ghz":{}}
        loop_over,add_time = self.report_analytics()
        for doc in self.client_doc_list:
            clients = doc.get('client_info')
            for client in clients:
                # separate calculation for grouping rxbyte
                if client.get('c_mac') and client['c_mac'] in self.maclist:
                    if client['client_interface'] == 'wlan0':
                        band = '2.4Ghz'
                    elif client['client_interface'] == 'wlan1':
                        band = '5Ghz'
                    if band not in band1_tmpdict:
                        band1_tmpdict[band] = {}
                    if doc['hour'] not in band1_tmpdict[band]:
                        band1_tmpdict[band][doc['hour']] = {}
                    if client['client_mac'] not in band1_tmpdict[band][doc['hour']]:
                        band1_tmpdict[band][doc['hour']][client['client_mac']] = 1
                    else:
                        band1_tmpdict[band][doc['hour']][client['client_mac']] += 1
        print band1_tmpdict
        for band in band1_tmpdict:
            result_band1=  {}
            result_band1['band'] = band
            result_band1['values'] = {count:0 for count in range(0,loop_over)}
            for hour in band1_tmpdict[band]:
                if hour in result_band1['values']:
                    result_band1['values'][hour] = len(band1_tmpdict[band][hour])
            clientBand.append(result_band1)
        
        return clientBand
    
    def time_grouping(self):
        import math
        from_time = self.gt
        to_time = self.lt
        from_time = datetime.datetime.utcfromtimestamp(from_time)
        to_time = datetime.datetime.utcfromtimestamp(to_time)
        thistime = to_time - from_time
        # calculating seconds and minutes
        total_secs = thistime.seconds
        secs = total_secs % 60
        total_mins = total_secs / 60
        mins = total_mins % 60
        hrs = total_mins / 60
        #rounding off hours, days, week , month on the basis of given timestamp
        month = 0
        week = 0
        hours = 0
        days = 0

        if secs > 0:
            mins += 1
            
        if self.type == "hours":
            hours = (thistime.days *24)+hrs if thistime.days>0 else hrs
            if mins > 0:
                hours += 1
                
        if self.type == "days":
            days = thistime.days
            if mins > 0:
                hrs += 1
            if hrs > 0:
                days += 1
        if self.type == "week":
            week = math.ceil(float(thistime.days)/float(7))if thistime.days >= 7 else 1
        if self.type == "month":
            month = math.ceil(float(thistime.days)/float(30)) if thistime.days >= 30 else 1
        
        date_dict = {"month":int(month),"week":int(week),"days":days,"hours":hours}
        return date_dict
        

class Stats():

    '''Common variable used under the class methods'''
    def __init__(self,**kwargs):

        
        self.lt= kwargs['lt'] if 'lt' in kwargs else None
        self.gt = kwargs['gt'] if 'gt' in kwargs else None
        self.maclist = kwargs['maclist'] if 'maclist' in kwargs else None
        self.client_doc_list = []
        
        qry = {}
        self.maclist = map(str.lower, self.maclist)
        if self.lt and self.gt and self.maclist:
            self.maclist = map(str.lower,self.maclist)
            qry["timestamp"] =  {"$gte": self.gt, "$lte": self.lt}
            qry['lower_snum'] = { "$in": self.maclist}
            qry['msolo_mac'] = {'$exists':1}
            print qry
            self.cl_cursor = DB.device_clients.find(qry).sort('_id',-1)
            for doc in self.cl_cursor:
                self.client_doc_list.append(doc)
        

    def clientThroughput(self):
        '''Calculating throughput on the basis of msolo client details  '''
        client_list = []
        result_list =  []
        unique_clients = {}
        for doc in self.client_doc_list:
                if doc.get('clients'):
                    client_details = {}
                    if doc['clients']['mac'] not in unique_clients:
                        unique_clients[doc['clients']['mac']] = True
                        client_details ['mac'] = doc['clients']['mac']
                        client_details ['throughput'] = doc['clients']['rxBytes']+doc['clients']['txBytes']
                        client_list.append(client_details)
        client_list =  sorted(client_list, key=itemgetter('throughput'),reverse = True)[:5]
        print "client_list",client_list        
        return client_list

    def clientTable(self):
        '''Calculating on the basis of Clients APids '''
        client_list = []
        unique_clients = {}
        for doc in self.client_doc_list:
            if doc.get('clients'):
                if doc['clients']['mac'] not in unique_clients:
                    unique_clients[doc['clients']['mac']] = True
                    client_list.append(doc['clients'])
        return client_list
            

def parse_request(GET):

    request_dict ={}
    response = {}

    for key in GET:

        request_dict[key] = ast.literal_eval(GET.get(key).strip()
                             ) if GET.get(key) else 0
    if "time" not in request_dict:
            response = {"status": "false","message": "No time stamp specified"}
    if "mac" not in request_dict:
            response = {"status": "false","message": "No MAC specified"}
    if not response and request_dict['time'][0] > request_dict['time'][1]:
            response = {"status": "false","message": "Wrong time range"}
    return request_dict,response


class ThroughputBand(View):

    def get(self, request):
        response_list = []
        maclist = []
        request_dict,response = parse_request(request.GET)
        if not response:
            if 'time' in request_dict and "mac" in request_dict:
                # API for gathering radio throughput data by band on <hourly> basis of timestamp and MAC
                maclist = request_dict['mac']
                obj = Hourly_Graph(maclist = maclist,gt=request_dict['time'][0],lt=request_dict['time'][1],type=request_dict.get('type') or 'hours')
                if not obj.radio_doc_list:
                    response = {"status": "false","data":[],"message": "No radio data found"}
                else:
                    response = {"status": "true","data":obj.thruBand(),"message": "Radio throughput by band"}
        return HttpResponse(json.dumps(response))
class ClientBand(View):

    def get(self, request):
        response_list = []
        maclist = []
        request_dict,response = parse_request(request.GET)
        if not response:
            if 'time' in request_dict and "mac" in request_dict:
                # API for gathering the msolo device clients by band on <hourly> basis of timestamp and MAC
                maclist = request_dict['mac']
                obj = Hourly_Graph(maclist = maclist,gt=request_dict['time'][0],lt=request_dict['time'][1],type=request_dict.get('type') or 'hours')
                if not obj.client_doc_list:
                    response = {"status": "false","data":[],"message": "No data found"}
                else:
                    response = {"status": "true","data":obj.clientBand(),"message": "Client by Band"}
        return HttpResponse(json.dumps(response))
class ClientThroughput(View):

    def get(self, request):
        response_list = []
        maclist = []
        request_dict,response = parse_request(request.GET)
        if not response:
            if 'time' in request_dict and "mac" in request_dict:
                # API for gathering msolo client throughput on timestamp and MAC
                maclist = request_dict['mac']
                obj = Stats(maclist = maclist,gt=request_dict['time'][0],lt=request_dict['time'][1],type=request_dict.get('type') or 'hours')
                if not obj.client_doc_list:
                    response = {"status": "false","data":[],"message": "No data found"}
                else:
                    response = {"status": "true","data":obj.clientThroughput(),"message": "Client throughput"}
        return  HttpResponse(json.dumps(response))
class ClientTable(View):

    def get(self, request):
        response_list = []
        maclist = []
        request_dict,response = parse_request(request.GET)
        if not response:
            if 'time' in request_dict and "mac" in request_dict:
                # API for gathering msolo client data on basis of timestamp and MAC
                maclist = request_dict['mac']
                obj = Stats(maclist = maclist,gt=request_dict['time'][0],lt=request_dict['time'][1])
                if not obj.client_doc_list:
                    response = {"status": "false","data":[],"message": "No data found"}
                else:
                    response = {"status": "true","data":obj.clientTable(),"message": "Client stats in table"}
        return HttpResponse(json.dumps(response))
