from pymongo import MongoClient
from django.http import HttpResponse
import datetime
import json
from django.views.generic.base import View
import ast
import csv, json
import random
from meru_device import settings
from collections import Counter
from random import randint
# Connection with mongoDB client

DB = settings.DB

utc_1970 = datetime.datetime(1970, 1, 1) #UTC since jan 1970
utc_now = datetime.datetime.utcnow() #UTC now


class Hourly_Device_Graph():

    '''Common variable used under the class methods'''
    def __init__(self,**kwargs):
        print "Memory Report"
        memory_report = self.memory_usage()
        print memory_report
        self.lt= kwargs['lt'] if 'lt' in kwargs else None
        self.gt = kwargs['gt'] if 'gt' in kwargs else None
        self.type = kwargs['type'] if 'type' in kwargs else None
        self.maclist = kwargs['maclist'] if 'maclist' in kwargs else None
        self.device_doc_list = []
        
        qry = {}
        self.maclist = map(str.lower, self.maclist)
        if self.lt and self.gt and self.maclist:
            lt = datetime.datetime.utcfromtimestamp(self.lt)
            gt = datetime.datetime.utcfromtimestamp(self.gt)
            #for mac in self.maclist:
            self.maclist = map(str.lower,self.maclist)
            qry["date"] =  {"$gte": gt, "$lte": lt}
            qry['c_info.c_mac'] = { "$in": self.maclist}
            print qry
            self.cl_cursor = DB.device_date_count.find(qry).sort('_id',-1)
            for doc in self.cl_cursor:
                self.device_doc_list.append(doc)
   
      
    def report_analytics (self,**kwargs):
        # to count the number of online aps for last 24 hours
        date_dict ={}
        date_dict=self.time_grouping()
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
    def DeviceReport(self, **kwargs):
        '''Calculating the number of devices  and device throughput'''
        result_dict = {'no_of_devices':{},'device_thru':{}}
        loop_over,add_time = self.report_analytics()
        to = self.gt
        for count in range(0,loop_over+1):
            frm = to
            to = to + add_time * 60 * 60
            device_thorughput = 0
            result_dict['no_of_devices'][count] =0
            result_dict['device_thru'][count] = 0
            unique_devices = {}
            
            for doc in self.device_doc_list:
                if doc['timestamp'] >= frm and doc['timestamp'] <= to:
                    devices  = doc.get('device_info')
                    for device in devices:
                        if device['device_mac'] not in unique_devices and device.get('c_mac') and  device['c_mac'] in self.maclist:
                            unique_devices[device['device_mac']] = 1
                            if device.get('device_rx') and device.get('device_tx'):
                                device_thorughput += device['device_rx']+device['device_tx']
                            result_dict['no_of_devices'][count] = len(unique_devices)
                            result_dict['device_thru'][count] = device_thorughput
            
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

class deviceGraph(View):

    def get(self, request):
        
        ''' API calls initaited for analtics graph page'''
        response_list = []
        maclist = []
        request_dict,response = parse_request(request.GET)
        if not response:
            
            if 'type' in request_dict and 'time' in request_dict and "mac" in request_dict:
                # API for gathering info about the analyitics point graph on the basis of timestamp and MAC
                maclist = request_dict['mac']
                obj = Hourly_Device_Graph(maclist = maclist,gt=request_dict['time'][0],lt=request_dict['time'][1],type=request_dict['type'] if 'type' in request_dict else None)
                response_list.append(obj.DeviceReport())
                response = HttpResponse(json.dumps({"status": "true","values":response_list,"message": "no.of devices and device thoughput"}))

        return response

