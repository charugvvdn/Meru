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
	print "Memory Report"
	memory_report = self.memory_usage()
	print memory_report
        self.lt= kwargs['lt'] if 'lt' in kwargs else None
        self.type = kwargs['type'] if 'type' in kwargs else None
        self.gt = kwargs['gt'] if 'gt' in kwargs else None
        self.maclist = kwargs['maclist'] if 'maclist' in kwargs else None
        self.ap_doc_list = []
        self.client_doc_list = []
        self.get_data = {}
        
        if self.lt and self.gt and self.maclist:
            for mac in self.maclist:
                # call for fetching clients document list
                self.cursor = DB.device_clients.find({ "lower_snum":mac.lower(), "timestamp": {"$gt": self.gt, "$lt": self.lt}}).sort('timestamp', -1)
                for doc in self.cursor:
                    self.client_doc_list.append(doc)
        
                # call for fetching aps document list
                self.cursor = DB.device_aps.find({ "lower_snum":mac.lower(),"timestamp": {"$gt": self.gt, "$lt": self.lt}}).\
                                    sort('timestamp', -1)
                for doc in self.cursor:
                    self.ap_doc_list.append(doc)
           

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
            
        
    def clientDeviceType(self, **kwargs):

        '''Calculating device type of clients '''
        device_dict = {"device_type":{"mac":0,"iphone":0,"ubuntu":0,"windows":0,"android":0}}
        unique_clients = {}
        
        for doc in self.client_doc_list:
            # get clients
            clients = doc.get('clients')
            if clients["mac"] not in unique_clients:
                if clients['clientType'].lower() in device_dict['device_type']:
                    device_dict['device_type'][clients['clientType'].lower()] += 1
                
                unique_clients[clients["mac"]] = 0
                
        
        return device_dict

    def busiestClients(self, **kwargs ):
        '''Calculating top 5 busiest clients '''
        busiest_dict = {"busiest_client":[]}
        result_list = []
        temp_dict = {}
        unique_clients = {}
        
        for doc in self.client_doc_list:
            # get clients
            clients = doc.get('clients')
            if clients["mac"] not in unique_clients:
                usage = clients['rxBytes']+clients['txBytes']
                unique_clients[clients["mac"]] = usage
                    
            else:
                if clients['rxBytes']+clients['txBytes'] > unique_clients[clients['mac']]:
                    usage = clients['rxBytes']+clients['txBytes']
                    unique_clients[clients['mac']] = usage
        temp_dict = sorted(unique_clients.values(),reverse=True)[:5] if len(unique_clients)>5 else unique_clients
        print temp_dict
        for mac in temp_dict:
            result_dict = {}
            result_dict['mac']= mac
            result_dict['usage'] =  temp_dict[mac]
            busiest_dict['busiest_client'].append(result_dict)
        return busiest_dict

    def report_analytics (self,**kwargs):
        # to count the number of online aps for last 24 hours
        date_dict ={}
        date_dict=self.time_grouping()
        from_time = self.gt
        to_time = self.lt
        result_dict = {"no_of_clients":{},"onlineAPs":{},"controller_thru":{}}
        to = from_time
        frm = from_time
        add_time = 0
        loop_over = 0
        print date_dict
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
        for count in range(0,loop_over):
            frm = to
            to = to + add_time * 60 * 60
            result_dict['no_of_clients'][count] =0
            result_dict['onlineAPs'][count] = 0
            result_dict['controller_thru'][count] = 0
            unique_client = {}
            unique_ap =  {}
            
            for doc in self.client_doc_list:
                if doc['timestamp'] >= frm and doc['timestamp'] <= to:
                    clients = doc.get('clients') 
                    if clients['mac'] not in unique_client:
                        unique_client[clients['mac']] = 0
                        result_dict['no_of_clients'][count] += 1
            for doc in self.ap_doc_list:
                if doc['timestamp'] >= frm and doc['timestamp'] <= to:
                    aps = doc.get('aps')
                    if aps['status'].lower() == 'up' and aps['mac'] not in unique_ap:
                        unique_client[aps['mac']] = 0
                        result_dict['onlineAPs'][count] += 1
                        # controller throughput to be revised with real values
                        result_dict['controller_thru'][count] = randint(20000,100000)
            
        return result_dict
        
        
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
            hours = thistime.days *24 if thistime.days>0 else hrs
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
            
            if 'type' in request_dict and 'time' in request_dict and "mac" in request_dict:
                # API for gathering info about the analyitics point graph on the basis of timestamp
                obj = AnalyticsReport(gt=request_dict['time'][0],lt=request_dict['time'][1],type=request_dict['type'] if 'type' in request_dict else None)
                response_list.append(obj.report_analytics())
                response = HttpResponse(json.dumps({"status": "true","values":response_list,"message": "onlineAPs, no.of clients and controller thoughput"}))
            elif 'time' in request_dict and "mac" in request_dict:
                # API for gathering detailed info about the analyitics point graph on timestamp and MAC list basis
                maclist = request_dict['mac']
                obj = AnalyticsReport(maclist = maclist, gt=request_dict['time'][0],lt=request_dict['time'][1])
                response_list.append(obj.busiestClients())
                response_list.append(obj.clientDeviceType())
                response = HttpResponse(json.dumps({"status": "true","values":response_list,"message": "Device type distribution and 5 busiest clients"}))

            
        return response
