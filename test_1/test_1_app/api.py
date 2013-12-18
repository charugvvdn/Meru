from django.http import HttpResponse, HttpResponseServerError
from pymongo import MongoClient
from django.shortcuts import render, render_to_response
from django.template import RequestContext
import datetime
import json
from django.views.generic.base import View
from views import Common
import ast
#Connection with mongodb client
client = MongoClient()
db = client['nms']

class HomeStats():
    def __init__(self):
        self.common = Common()
        self.post_data = {}
        self.mac_list=[]
        self.doc_list = []
        self.response = []
        self.result_dict = {}
        utc_1970 = datetime.datetime(1970, 1, 1)
        utc_now = datetime.datetime.utcnow()
        offset = utc_now - datetime.timedelta(minutes=30)
        
        
    def access_pt_util(self,doc_list,p_data,typeof="aps"):
        '''#---------------b. SITES WITH VERY HIGH ACCESS POINT UTILIZATION------------#'''
        mac_list = []
        threshhold_max = 0
        if 'threshhold' in p_data:
            threshhold = post_data['threshhold']
            threshhold_min = threshhold[0]
            threshhold_max = threshhold[1]

        else:
            threshhold_min = int(0)
            threshhold_max = int(78799)

        for doc in doc_list:
            mac = doc['snum']
            flag = 0
            rx_tx = 0
            if typeof in doc['msgBody'].get('controller'):
                aps = doc.get('msgBody').get('controller').get(typeof)
                for ap in aps:
                    rx_tx = ap['rxBytes']+ap['txBytes']
                    if rx_tx > threshhold_max:
                        flag   = 1 
                if flag and mac not in mac_list:
                    mac_list.append(mac)
        self.result_dict["access_pt"] = {}
        self.result_dict["access_pt"]['message'] = "SITES WITH VERY HIGH ACCESS POINT UTILIZATION"
        self.result_dict["access_pt"]['count'] = len(mac_list)
        self.result_dict["access_pt"]['status'] = True
        self.result_dict["access_pt"]['mac'] = mac_list
        print self.result_dict['access_pt']

        '''#---------------b. SITES WITH VERY HIGH ACCESS POINT UTILIZATION------------#'''


    def sites_down(self,doc_list,typeof="aps"):
        '''#---------------b. SITES WITH DEVICES DOWN------------#'''
        mac_list = []
        for doc in doc_list:
            mac = doc['snum']
            flag = 0
            
            if typeof in doc['msgBody'].get('controller'):
                aps = doc.get('msgBody').get('controller').get(typeof)
                for ap in aps:
                    
                    if ap['status'] == 'DOWN':
                        flag   = 1 
                if flag and mac not in mac_list:
                    mac_list.append(mac)
        self.result_dict["sites_down"] = {}
        self.result_dict["sites_down"]['message'] = "SITES WITH DEVICES DOWN"
        self.result_dict["sites_down"]['count'] = len(mac_list)
        self.result_dict["sites_down"]['status'] = True
        self.result_dict["sites_down"]['mac'] = mac_list
        print self.result_dict["sites_down"]

        '''#---------------b. SITES WITH DEVICES DOWN------------#'''

    def critical_alarms(self,doc_list,typeof="alarms"):
        '''#---------------b. SITES WITH CRITICAL ALARMS------------#'''
        mac_list = []
        for doc in doc_list:
            mac = doc['snum']
            flag = 0
            
            if typeof in doc['msgBody'].get('controller'):
                alarms = doc.get('msgBody').get('controller').get(typeof)
                for alarm in alarms:
                    
                    if alarm['severity'] == 'High':
                        flag   = 1 
                if flag and mac not in mac_list:
                    mac_list.append(mac)
        self.result_dict["critical_alarm"] = {}
        self.result_dict["critical_alarm"]['message'] = "SITES WITH CRITICAL ALARMS"
        self.result_dict["critical_alarm"]['count'] = len(mac_list)
        self.result_dict["critical_alarm"]['status'] = True
        self.result_dict["critical_alarm"]['mac'] = mac_list
        print self.result_dict["critical_alarm"]

        '''#---------------b. SITES WITH CRITICAL ALARMS------------#'''

    def wireless_stats(self, p_data, typeof="aps"):
        '''#------------------------a. SITES WITH DECREASE IN WIRELESS EXPERIENCES----------------#'''
        wifiexp_ap_sum = 0
        aps_count = 0
        avg_doc_wifiexp = 0
        avg_controller = 0
        final_avg_controller = 0
        doc_list = []
        flag = 0
        controller_list = []
        mac_list = p_data['mac']
        
        if 'time' in p_data:
            time_frame = p_data['time']
            start_time = time_frame[0]
            end_time = time_frame[1]

        else:
            utc_1970 = datetime.datetime(1970, 1, 1)
            utc_now = datetime.datetime.utcnow()
            offset = utc_now - datetime.timedelta(minutes=30)
            start_time = int((offset - utc_1970).total_seconds())
            end_time = int((utc_now - utc_1970).total_seconds())
        
        for mac in mac_list:
            
            doc_list = []
            
            cursor = db.devices.find({"snum": mac, "timestamp" \
                : {"$gt": start_time, "$lt": end_time}}).sort('timestamp',-1)
            res = cursor.count()
            if res == 0:
                continue
            import pprint
            avg_controller  = 0
            for doc in cursor:
                doc_list.append(doc)
                pprint.pprint(doc)

            for doc in doc_list:
                
                wifiexp_ap_sum = 0
                aps_count = 0
                
                if typeof in doc['msgBody'].get('controller'):
                    aps = doc.get('msgBody').get('controller').get(typeof)
                    for ap in aps:
                        wifiexp_ap_sum += ap['wifiExp']
                        aps_count += 1
                    
                    avg_doc_wifiexp =  wifiexp_ap_sum / aps_count
                    avg_controller += avg_doc_wifiexp
            final_avg_controller = avg_controller/len(doc_list)
            last_doc = doc_list[0].get('msgBody').get('controller').get(typeof)
            flag = 0
            for ap in last_doc:
                if ap['wifiExp']-final_avg_controller < 0:
                    flag = 1
            if flag:
                controller_list.append(doc_list[0]['snum'])
            

            
            
        self.result_dict["wifi_exp"] = {}
        self.result_dict["wifi_exp"]['message'] = "SITES WITH DECREASE IN WIRELESS EXPERIENCES"
        self.result_dict["wifi_exp"]['count'] = len(controller_list)
        self.result_dict["wifi_exp"]['status'] = True
        self.result_dict["wifi_exp"]['mac'] = controller_list
        print self.result_dict['wifi_exp']
        '''#------------------------a. SITES WITH DECREASE IN WIRELESS EXPERIENCES----------------#'''

class HomeApi(View):
    def get(self, request,*args, **kwargs):
        
        home_stats = HomeStats()
        
        for key in request.GET:
            home_stats.post_data[key] = ast.literal_eval(request.GET.get(key).strip())

        if 'mac' not in home_stats.post_data:
            return HttpResponse(json.dumps({"status": "false", \
                "message": "No MAC data"}))
        else:
            #fetch the docs
            doc_list = home_stats.common.let_the_docs_out(home_stats.post_data)
        

        #------------------------a. SITES WITH DECREASE IN WIRELESS EXPERIENCES----------------#
        home_stats.wireless_stats(home_stats.post_data)
        #------------------------
        #---------------b. SITES WITH VERY HIGH ACCESS POINT UTILIZATION------------#
        home_stats.access_pt_util(doc_list,home_stats.post_data)
        #-------------------------
        #---------------b. SITES WITH DEVICES DOWN------------#
        home_stats.sites_down(doc_list)
        #--------------------------
        #---------------b. SITES WITH CRITICAL ALARMS------------#
        home_stats.critical_alarms(doc_list)
        #----------------------------
        return HttpResponse(json.dumps({"status": "OK" }))
        

        


        
