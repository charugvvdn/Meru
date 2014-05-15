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
        self.ap_doc_list = []
        self.client_doc_list = []
        
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
            self.cl_cursor = DB.client_date_count.find(qry).sort('_id',-1)
            self.ap_cursor = DB.ap_date_count.find(qry).sort('_id',-1)
            for doc in self.cl_cursor:
                self.client_doc_list.append(doc)
            for doc in self.ap_cursor:
                self.ap_doc_list.append(doc)   
      
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
    def SSID(self, **kwargs):

        '''Calculating on the basis of client's ssid '''
        SSID = []
        top_ssid = []
        toal_ssid_list = []
        sorted_ssid_list = []
        ssid_tempdict = {}
        loop_over,add_time = self.report_analytics()
        for doc in self.client_doc_list:
                clients = doc.get('client_info')
                for client in clients:

                    # separate calculation for grouping ssid
                    if client['client_ssid'] not in ssid_tempdict:
                        ssid_tempdict[client['client_ssid']] = {}
                    if doc['hour'] not in ssid_tempdict[client['client_ssid']]:
                        ssid_tempdict[client['client_ssid']][doc['hour']] = 1
                    else:
                        ssid_tempdict[client['client_ssid']][doc['hour']] += 1
        
        for ssid in ssid_tempdict:
            result_ssid = {}
            result_ssid['name'] = ssid
            result_ssid['values'] = {count:0 for count in range(0,loop_over)}
            print "values",result_ssid['values']
            result_ssid['total_count'] = 0
            for hour in ssid_tempdict[ssid]:
                if hour in result_ssid['values']:
                    result_ssid['values'][hour] = ssid_tempdict[ssid][hour]
                result_ssid['total_count'] += ssid_tempdict[ssid][hour]
            SSID.append(result_ssid)
        for ssid in SSID:
            toal_ssid_list.append(ssid['total_count'])
        sorted_ssid_list = sorted(toal_ssid_list,reverse = True)[:5]
        for item in SSID:
            if item['total_count'] in sorted_ssid_list:
                top_ssid.append(item)

            
        return top_ssid

    def rfBand(self, **kwargs):

        '''Calculating on the basis of client's rfband '''
        rfBand = []
        rfBand2 = []
        RFBand_result = {'rfband1':0,'rfband2':0}
        rfband_tempdict = {}
        rfband_dict = {}
        loop_over,add_time = self.report_analytics()
        for doc in self.client_doc_list:
                clients = doc.get('client_info')
                for client in clients:
                    # separate calculation for grouping rfband
                    if client.get('client_band') and  client.get('client_band') not in rfband_tempdict:
                        rfband_tempdict[client['client_band']] = {}
                    if doc['hour'] not in rfband_tempdict[client['client_band']]:
                        rfband_tempdict[client['client_band']][doc['hour']] = 1
                    else:
                        rfband_tempdict[client['client_band']][doc['hour']] += 1

                    #grouping rfBand
                    if client.get('client_ssid') and client.get('client_ssid') not in rfband_dict:
                        rfband_dict[client['client_ssid']] = {}
                    if client['client_band'] not in rfband_dict[client['client_ssid']]:
                        rfband_dict[client['client_ssid']][client['client_band']] = 1
                    else:
                        rfband_dict[client['client_ssid']][client['client_band']] += 1
        print "rfband_dict",rfband_dict
        for rfband in rfband_tempdict:
            
            result_rfband = {"name":"","values":{count:0 for count in range(0,loop_over)}}
            result_rfband['name'] = rfband
            for hour in rfband_tempdict[rfband]:
                if hour in result_rfband['values']:
                    result_rfband['values'][hour] = rfband_tempdict[rfband][hour]
            rfBand.append(result_rfband)

        for ssid in rfband_dict:
            ssid_dict = {'ssid_name':'','rfband':[]}
            ssid_dict['ssid_name'] = ssid
            for rfband in rfband_dict[ssid]:
                tmp_dict = {}
                tmp_dict['rfband_name'] = rfband
                tmp_dict['value'] = rfband_dict[ssid][rfband]
                ssid_dict['rfband'].append(tmp_dict)
                
            rfBand2.append(ssid_dict)
        RFBand_result['rfband1'] = rfBand
        RFBand_result['rfband2'] = rfBand2
        return RFBand_result

    def clientThroughput(self, **kwargs): 
        '''Calculating on the basis of client's rx and tx bytes '''
        Throughput = {}
        rx_tempdict = {}
        tx_tempdict = {}
        loop_over,add_time = self.report_analytics()
        for doc in self.client_doc_list:
            clients = doc.get('client_info')
            for client in clients:
                # separate calculation for grouping rxbyte
                if doc['hour'] not in rx_tempdict:
                    rx_tempdict[doc['hour']] = client['client_rx']
                else:
                    rx_tempdict[doc['hour']] += client['client_rx']
                # separate calculation for grouping txbyte
                if doc['hour'] not in tx_tempdict:
                    tx_tempdict[doc['hour']] = client['client_tx']
                else:
                    tx_tempdict[doc['hour']] += client['client_tx']

        result_rxbyte = {count:0 for count in range(0,loop_over)}
        for hour in rx_tempdict:
            if hour in result_rxbyte:
                result_rxbyte[hour] = rx_tempdict[hour]
        

        result_txbyte = {count:0 for count in range(0,loop_over)}
        for hour in tx_tempdict:
            if hour in result_txbyte:
                result_txbyte[hour] = tx_tempdict[hour]

        Throughput['rx'] = result_rxbyte
        Throughput['tx'] = result_txbyte
        return Throughput
    def ApState(self, **kwargs):

        '''Calculating on the basis of ap's status '''
        ApState = {}
        online_tempdict = {}
        offline_tempdict = {}
        total_online = 0
        total_offline = 0
        loop_over,add_time = self.report_analytics()
        for doc in self.ap_doc_list:
            aps = doc.get('ap_info')
            for ap in aps:
                # separate calculation for grouping online offline aps
                if ap['ap_status'].lower() == 'up':
                    if doc['hour'] not in online_tempdict:
                        online_tempdict[doc['hour']] = 1
                    else:
                        online_tempdict[doc['hour']] += 1
                    total_online += online_tempdict[doc['hour']]
                elif ap['ap_status'].lower() == 'down':
                    if doc['hour'] not in offline_tempdict:
                        offline_tempdict[doc['hour']] = 1
                    else:
                        offline_tempdict[doc['hour']] += 1
                    total_offline += offline_tempdict[doc['hour']]

        result_onlineAP  = {count:0 for count in range(0,loop_over)}
        for hour in online_tempdict:
            if hour in result_onlineAP:
                result_onlineAP[hour] = online_tempdict[hour]

        result_offlineAP = {count:0 for count in range(0,loop_over)}
        for hour in offline_tempdict:
            if hour in result_offlineAP:
                result_offlineAP[hour] = offline_tempdict[hour]
        ApState['onlineAP'] = result_onlineAP   
        ApState['offlineAP'] = result_offlineAP
        ApState['totalOffline'] = total_offline
        ApState['totalOnline'] = total_online
        return ApState


        
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
        self.ap_doc_list = []
        self.client_doc_list = []
        
        qry = {}
        self.maclist = map(str.lower, self.maclist)
        if self.lt and self.gt and self.maclist:
            self.maclist = map(str.lower,self.maclist)
            qry["timestamp"] =  {"$gte": self.gt, "$lte": self.lt}
            qry['lower_snum'] = { "$in": self.maclist}
            print qry
            self.cl_cursor = DB.client_stats.find(qry).sort('_id',-1)
            self.ap_cursor = DB.ap_stats.find(qry).sort('_id',-1)
            for doc in self.cl_cursor:
                self.client_doc_list.append(doc)
            for doc in self.ap_cursor:
                self.ap_doc_list.append(doc)           

    def ApModel(self):
        '''Calculating on the basis of AP Model '''
        ApModel = []
        ap_count = {}
        
        temp_list = []
        result_list =  []
        for doc in self.ap_doc_list:
                # separate calculation for grouping Model of aps
                if doc.get('model'):
                    temp_list.append(doc['model'])
                    ap_count = Counter(temp_list)
        print "ap_count",ap_count
        for key,count in ap_count.iteritems():
            values = {}
            values['name'] = key
            values['value'] = count
            ApModel.append(values)
        return ApModel

    def ClientAPid(self):
        '''Calculating on the basis of Clients APids '''
        Client = {}
        data1 = []
        data2 = {"0-15":[],"15-75":[],">75":[]}
        temp_list = []
        client_apid_list = []
        result_list =  []
        apid_count = {}
        for doc in self.client_doc_list:
                # separate calculation for grouping Apid of clients
                if doc.get('ap_id'):
                    temp_list.append(doc['ap_id'])
                    apid_count = Counter(temp_list)
        print "temp_list",temp_list
        for key,count in apid_count.iteritems():
            values = {}

            values['name'] = key
            values['value'] = count
            data1.append(values)
            if count > 0 and count <= 15:
                data2["0-15"].append(key)
            elif count > 15 and count <= 75:
                data2["15-75"].append(key)
            else:
                data2[">75"].append(key)
        Client['data1'] = data1
        Client['data2'] = data2
        return Client
            

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

class SSID_graph(View):

    def get(self, request):
        response_list = []
        maclist = []
        request_dict,response = parse_request(request.GET)
        if not response:
            if 'time' in request_dict and "mac" in request_dict:
                # API for gathering info about the device graphs on <hourly> basis of timestamp and MAC
                maclist = request_dict['mac']
                obj = Hourly_Graph(maclist = maclist,gt=request_dict['time'][0],lt=request_dict['time'][1],type=request_dict.get('type') or 'hours')
                if not obj.client_doc_list:
                    response = {"status": "false","data":[],"message": "No data found"}
                else:
                    response = {"status": "true","data":obj.SSID(),"message": "SSID"}
                
        return HttpResponse(json.dumps(response))
class rfBand_graph(View):

    def get(self, request):
        response_list = []
        maclist = []
        request_dict,response = parse_request(request.GET)
        if not response:
            if 'time' in request_dict and "mac" in request_dict:
                # API for gathering info about the device graphs on <hourly> basis of timestamp and MAC
                maclist = request_dict['mac']
                obj = Hourly_Graph(maclist = maclist,gt=request_dict['time'][0],lt=request_dict['time'][1],type=request_dict.get('type') or 'hours')
                if not obj.client_doc_list:
                    response = {"status": "false","data":[],"message": "No data found"}
                else:
                    response = {"status": "true","data":obj.rfBand(),"message": "rfBand"}
        return HttpResponse(json.dumps(response))
class Throughput_graph(View):

    def get(self, request):
        response_list = []
        maclist = []
        request_dict,response = parse_request(request.GET)
        if not response:
            if 'time' in request_dict and "mac" in request_dict:
                # API for gathering info about the device graphs on <hourly> basis of timestamp and MAC
                maclist = request_dict['mac']
                obj = Hourly_Graph(maclist = maclist,gt=request_dict['time'][0],lt=request_dict['time'][1],type=request_dict.get('type') or 'hours')
                if not obj.client_doc_list:
                    response = {"status": "false","data":[],"message": "No data found"}
                else:
                    response = {"status": "true","data":obj.clientThroughput(),"message": "Throughput"}
        return HttpResponse(json.dumps(response))
class ApState_graph(View):

    def get(self, request):
        response_list = []
        maclist = []
        request_dict,response = parse_request(request.GET)
        if not response:
            if 'time' in request_dict and "mac" in request_dict:
                # API for gathering info about the device graphs on <hourly> basis of timestamp and MAC
                maclist = request_dict['mac']
                obj = Hourly_Graph(maclist = maclist,gt=request_dict['time'][0],lt=request_dict['time'][1],type=request_dict.get('type') or 'hours')
                if not obj.ap_doc_list:
                    response = {"status": "false","data":[],"message": "No data found"}
                else:
                    response = {"status": "true","data":obj.ApState(),"message": "ApState"}
        return  HttpResponse(json.dumps(response))
class ApModel_graph(View):

    def get(self, request):
        response_list = []
        maclist = []
        request_dict,response = parse_request(request.GET)
        if not response:
            if 'time' in request_dict and "mac" in request_dict:
                # API for gathering info about the device graphs on <hourly> basis of timestamp and MAC
                maclist = request_dict['mac']
                obj = Stats(maclist = maclist,gt=request_dict['time'][0],lt=request_dict['time'][1])
                if not obj.ap_doc_list:
                    response = {"status": "false","data":[],"message": "No data found"}
                else:
                    response = {"status": "true","data":obj.ApModel(),"message": "ApModel"}
        return HttpResponse(json.dumps(response))
class ClientAPid_graph(View):

    def get(self, request):
        response_list = []
        maclist = []
        request_dict,response = parse_request(request.GET)
        if not response:
            if 'time' in request_dict and "mac" in request_dict:
                # API for gathering info about the device graphs on <hourly> basis of timestamp and MAC
                maclist = request_dict['mac']
                obj = Stats(maclist = maclist,gt=request_dict['time'][0],lt=request_dict['time'][1])
                if not obj.client_doc_list:
                    response = {"status": "false","data":[],"message": "No data found"}
                else:
                    response = {"status": "true","data":obj.ClientAPid(),"message": "ClientApid"}
                
        return HttpResponse(json.dumps(response))
