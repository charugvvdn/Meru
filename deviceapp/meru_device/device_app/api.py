from pymongo import MongoClient
import datetime
from views import Common
import pymongo
from collections import Counter
import itertools
# Connection with mongoDB client
try:
    CLIENT = MongoClient()
    DB = CLIENT['nms']
except pymongo.errors.PyMongoError, e:
    print "api.py -->"
    print e

UTC_1970 = datetime.datetime(1970, 1, 1)
UTC_NOW = datetime.datetime.utcnow()
OFFSET = UTC_NOW - datetime.timedelta(minutes=30)
class DashboardStats():

    '''Common variable used under the class methods'''

    def __init__(self,**kwargs):
        print "Memory Report"
        memory_report = self.memory_usage()
        print memory_report
        self.lt= kwargs['lt'] if 'lt' in kwargs else None
        self.gt = kwargs['gt'] if 'gt' in kwargs else None
        self.reporttype= kwargs['reportType'] if 'reportType' in kwargs else 0
        self.maclist = kwargs['maclist'] if 'maclist' in kwargs else None
        self.ap_doc_list = []
        self.alarm_doc_list = []
        self.client_doc_list = []
        self.controller_doc_list = []

        qry = {}
        self.maclist = map(str.lower, self.maclist)
        if self.lt and self.gt and self.maclist:
            #for mac in self.maclist:
            self.maclist = map(str.lower,self.maclist)
            qry["timestamp"] =  {"$gte": self.gt, "$lte": self.lt}
            qry['lower_snum'] = { "$in": self.maclist}
            self.controller_cursor = DB.controller_stats.find(qry).sort('_id',-1)
            self.cl_cursor = DB.client_stats.find(qry).sort('_id',-1)
            self.ap_cursor = DB.ap_stats.find(qry).sort('_id',-1)
            self.alarm_cursor = DB.device_alarms.find(qry).sort('_id',-1)
            for doc in self.controller_cursor:
                self.controller_doc_list.append(doc)
            for doc in self.cl_cursor:
                self.client_doc_list.append(doc)
            for doc in self.ap_cursor:
                self.ap_doc_list.append(doc)
            for doc in self.alarm_cursor:
                self.alarm_doc_list.append(doc)           

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

    def number_stations(self, **kwargs ):
        '''API calculating NUMBER OF STATIONS '''
        result_dict = {}
        online_clients = []
        critical_clients = []
        unique_clients = {}

        for doc in self.client_doc_list:
            if doc.get('client_mac') and doc.get('state'):
                client_mac = doc['client_mac']
                client_state = doc['state'].lower()
                if client_mac not in unique_clients:
                    unique_clients[client_mac] = 0
                    if client_state == 'associated':
                        online_clients.append(client_mac)
                    else:
                        critical_clients.append(client_mac)
        result_dict['label'] = 'Number of stations'
        result_dict['data'] = [len(online_clients), len(critical_clients)]
        if self.reporttype == 1:
            result_dict['station_list'] = [online_clients, critical_clients]
        return result_dict

    def number_controllers(self, **kwargs ):
        '''API calculating NUMBER OF Controllers '''
        count = 0
        result_dict = {}
        unique_mac = {}
        for doc in self.controller_doc_list:
            if doc.get('lower_snum'):
                mac = doc['lower_snum']
                if mac not in unique_mac:
                    unique_mac[mac] = 0
        result_dict['label'] = 'Number of controllers'
        result_dict['data'] = len(unique_mac)
        if self.reporttype == 1:
            result_dict['maclist'] = [unique_mac.keys()]
        return result_dict

    def wifi_exp(self, **kwargs):
        '''API calculating WI-FI EXPERIENCE '''
        count = 0
        wifi_client = 0
        result_dict = {}
        result_dict['label'] = 'Wifi experience'
        result_dict['data'] = 0
        return result_dict

    def online_offline_aps(self, **kwargs ):
        '''API calculating NUMBER OF APS '''
        result_dict = {}
        online_aplist = []
        offline_aplist = []
        unique_aps = {}
        for doc in self.ap_doc_list:
            if doc.get('ap_mac') and doc.get('status'):
                ap_mac = doc['ap_mac']
                ap_status = doc['status'].lower()
                if ap_mac not in unique_aps:
                    unique_aps[ap_mac] = 0
                    if ap_status == 'up':
                        online_aplist.append(ap_mac)
                    else:
                        offline_aplist.append(ap_mac)
        result_dict['label'] = 'Number of online offline aps'
        result_dict['data'] = [len(online_aplist), len(offline_aplist)]
        if self.reporttype == 1:
            result_dict['aplist'] = [online_aplist, offline_aplist]
        return result_dict

    def alarms_count(self, **kwargs ):
        
        '''API calculating critical, high, minor alarms'''
        result_dict = {}
        high_alarm = []
        critical_alarm = []
        minor_alarm  = []
        for doc in self.alarm_doc_list:
            if  doc.get('lower_snum') and doc.get('alarms'):
                mac = doc['lower_snum']
                for alarm in doc.get('alarms'):
                    alarm_status = alarm.get('severity').lower()
                    if alarm_status == 'high':
                        high_alarm.append(mac)
                    elif alarm_status == 'critical':
                        critical_alarm.append(mac)
                    elif alarm_status == 'low':
                        minor_alarm.append(mac)
        result_dict['label'] = 'Alarms'
        result_dict['data'] = [len(critical_alarm), len(high_alarm), len(minor_alarm)]
        if self.reporttype == 1:
            result_dict['maclist'] = [{"critical":critical_alarm, \
             "high":high_alarm, "minor":minor_alarm}]
        return result_dict


class HomeStats():

    '''Common variable used under the class methods'''

    def __init__(self,**kwargs):
        print "Memory Report"
        memory_report = self.memory_usage()
        print memory_report
        self.lt= kwargs['lt'] if 'lt' in kwargs else None
        self.gt = kwargs['gt'] if 'gt' in kwargs else None
        self.reporttype= kwargs['reportType'] if 'reportType' in kwargs else 0
        self.maclist = kwargs['maclist'] if 'maclist' in kwargs else None
        self.ap_doc_list = []
        self.alarm_doc_list = []
        self.client_doc_list = []
        self.controller_doc_list = []

        qry = {}
        self.maclist = map(str.lower, self.maclist)
        if self.lt and self.gt and self.maclist:
            #for mac in self.maclist:
            self.maclist = map(str.lower,self.maclist)
            qry["timestamp"] =  {"$gte": self.gt, "$lte": self.lt}
            qry['lower_snum'] = { "$in": self.maclist}
            self.controller_cursor = DB.controller_stats.find(qry).sort('_id',-1)
            self.cl_cursor = DB.client_stats.find(qry).sort('_id',-1)
            self.ap_cursor = DB.ap_stats.find(qry).sort('_id',-1)
            self.alarm_cursor = DB.device_alarms.find(qry).sort('_id',-1)
            for doc in self.controller_cursor:
                self.controller_doc_list.append(doc)
            for doc in self.cl_cursor:
                self.client_doc_list.append(doc)
            for doc in self.ap_cursor:
                self.ap_doc_list.append(doc)
            for doc in self.alarm_cursor:
                self.alarm_doc_list.append(doc)           
        
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

    def access_pt_util(self, **kwargs):
        '''b. SITES WITH VERY HIGH ACCESS POINT UTILIZATION'''
        mac_list = []
        controller_dict = {}
        result_dict = {}
        sites_count = 0
        apid_list = []
        count_apid = {}
        for doc in self.client_doc_list:
            if doc.get('lower_snum') and doc.get('ap_id'):
                mac = doc['lower_snum']
                if mac not in controller_dict:
                    controller_dict[mac] = []
                client_apid = doc['ap_id']
                controller_dict[mac].append(client_apid)
                

        print controller_dict
        for mac in controller_dict:
            count_apid = Counter(controller_dict[mac])
        print count_apid
        for key,count in count_apid.iteritems():
            if count > 30:
                sites_count += 1
                break
        

        result_dict["access_pt"] = {}
        result_dict["access_pt"]['message'] = \
            "SITES WITH VERY HIGH ACCESS POINT UTILIZATION"
        result_dict["access_pt"]['count'] = sites_count
        result_dict["access_pt"]['status'] = True
        if self.reporttype == 1:
            result_dict["access_pt"]['mac'] = controller_dict.keys()
        return result_dict['access_pt']

    def change_security(self, **kwargs):
        ''' API Calculating change in security # '''
        result_dict = {}
        mac_list = []
        count = 0
        for doc in self.controller_doc_list:
            if doc.get('lower_snum') and doc.get('secState'):
                mac = doc['lower_snum']
                security_state  = doc['secState']
                if int(security_state) == 1 and mac not in mac_list:
                    mac_list.append(mac)

        result_dict["change_security"] = {}
        result_dict["change_security"]['message'] = \
            "SITES WITH CHANGE IN SECURITY"
        result_dict["change_security"]['count'] = len(mac_list)
        result_dict["change_security"]['status'] = True
        if self.reporttype == 1 :
            result_dict["change_security"]['mac'] = mac_list
        return result_dict['change_security']

    def sites_critical_health(self, **kwargs):
        '''SITES WITH CRITICAL HEALTH'''
        result_dict = {}
        mac_list = []
        # logic to be implemneted

        result_dict["sites_critcal_health"] = {}
        result_dict["sites_critcal_health"]['message'] = \
            "SITES WITH CRITICAL HEALTH"
        result_dict["sites_critcal_health"]['count'] = 0
        result_dict["sites_critcal_health"]['status'] = True
        if self.reporttype == 1:
            result_dict["sites_critcal_health"]['mac'] = mac_list
        return result_dict["sites_critcal_health"]

    def sites_down(self, **kwargs):
        '''b. SITES WITH DEVICES DOWN'''
        result_dict = {}
        mac_list = []
        typeof = "aps"
        for doc in self.ap_doc_list:
            if doc.get('lower_snum') and doc.get('status'):
                mac = doc['lower_snum']
                ap_status = doc['status'].lower()
                if ap_status == 'down' and mac not in mac_list:
                    mac_list.append(mac)
        result_dict["sites_down"] = {}
        result_dict["sites_down"]['message'] = "SITES WITH DEVICES DOWN"
        result_dict["sites_down"]['count'] = len(mac_list)
        result_dict["sites_down"]['status'] = True
        if self.reporttype == 1 :
            result_dict["sites_down"]['mac'] = mac_list
        return result_dict["sites_down"]

    def critical_alarms(self, **kwargs):
        '''SITES WITH CRITICAL ALARMS'''
        result_dict = {}
        mac_list = []
        for doc in self.alarm_doc_list:
            if doc.get('lower_snum') and doc.get('alarms'):
                mac = doc['lower_snum']
                for alarm in doc.get('alarms'):
                    alarm_status = alarm.get('severity').lower()
                    if alarm_status  == 'critical' and mac not in mac_list:
                        mac_list.append(mac)
        result_dict["critical_alarm"] = {}
        result_dict["critical_alarm"]['message'] = \
            "SITES WITH CRITICAL ALARMS"
        result_dict["critical_alarm"]['count'] = len(mac_list)
        result_dict["critical_alarm"]['status'] = True
        if self.reporttype == 1:
            result_dict["critical_alarm"]['mac'] = mac_list
        return result_dict["critical_alarm"]

    def controller_util(self, **kwargs ):
        '''API calculating controller utilization count'''
        lt_50_count = 0
        _50_75_count = 0
        lt_75_count = 0
        result_dict = {}
        unique_mac = {}
        for doc in self.controller_doc_list:
            if doc.get('lower_snum') and doc.get('controllerUtil'):
                mac = doc['lower_snum']
                controller_util = int(doc['controllerUtil'])
                if mac not in unique_mac:
                    unique_mac[mac] = 0
                    if controller_util < 50:
                        lt_50_count += 1
                    elif controller_util > 50 and controller_util <= 75:
                        _50_75_count += 1
                    else:
                        lt_75_count += 1

        result_dict['label'] = 'Controller Utilization'
        result_dict['data'] = [lt_50_count, _50_75_count, lt_75_count]
        return result_dict

    def alarms(self, **kwargs ):
        '''API calculating critical, high, minor alarms'''
        result_dict = {}
        high_alarm = []
        critical_alarm = []
        minor_alarm  = []
        for doc in self.alarm_doc_list:
            if doc.get('lower_snum') and doc.get('alarms'):
                mac = doc['lower_snum']
                for alarm in doc.get('alarms'):
                    alarm_status = alarm.get('severity').lower()
                    if alarm_status == 'high':
                        high_alarm.append(mac)
                    elif alarm_status == 'critical':
                        critical_alarm.append(mac)
                    elif alarm_status == 'low':
                        minor_alarm.append(mac)
        result_dict['label'] = 'Alarms'
        result_dict['data'] = [len(critical_alarm), len(high_alarm), len(minor_alarm)]
        if self.reporttype == 1:
            result_dict['maclist'] = [{"critical":critical_alarm, \
             "high":high_alarm, "minor":minor_alarm}]
        return result_dict

    def access_points(self, **kwargs):
        ''' API Calculating online, offline, down aps # '''
        result_dict = {}
        unique_ap = {}
        offline_maclist = []
        online_maclist = []

        for doc in self.ap_doc_list:
            if doc.get('ap_mac') and doc.get('status'):
                ap_status = doc['status'].lower()
                ap_mac = doc['ap_mac']
                if ap_mac not in unique_ap:
                    unique_ap[ap_mac] = 0
                    if ap_status == 'down':
                        offline_maclist.append(ap_mac)
                    else:
                        online_maclist.append(ap_mac)

        result_dict['label'] = 'Access point'
        result_dict['data'] = [len(online_maclist), len(offline_maclist), 0]
        if self.reporttype == 1:
            result_dict['maclist'] = [{"online":online_maclist, \
             "offline":offline_maclist, "down":[]}]
        return result_dict

    def wireless_clients(self, **kwargs):
        ''' API Calculating wireless clients count according to timestamp '''
        peak_list = []
        peak_maclist = []
        result_dict = {}
        current_clients = []
        max_client = 0
        avg_client = 0
        # getting the number of clients in controller which are added last in the db (latest timestamp)
        if len(self.client_doc_list) > 0:
            doc = self.client_doc_list[0]
            current_time = doc.get('timestamp')
            for doc in self.client_doc_list:
                if  doc.get('lower_snum') and doc.get('client_mac'):
                    client_mac = doc['client_mac']
                    time = doc['timestamp']
                    if time == current_time and client_mac not in current_clients:
                        current_clients.append(client_mac)
        # getting the highest number of clients against the controller added between the given time range
        all_clients = [{key,len(list(val))} for key, val in itertools.groupby(self.client_doc_list, lambda v: v['lower_snum'])]
	all_clients = dict(sorted(x,key=lambda k:isinstance(k,int),reverse=True) for x in all_clients)
	print "---all clients--"
	print all_clients
        for mac_iter in all_clients:
            peak_list.append(mac_iter)
            peak_maclist.append(all_clients[mac_iter])
        result_dict['label'] = 'Wireless Clients'
        print "peak list",peak_list
        if len(peak_list) > 0:
            max_client = max(peak_list)
            avg_client = sum(peak_list) / len(peak_list)
        result_dict['data'] = [len(current_clients), max_client, avg_client ]
        
        if self.reporttype:
            result_dict['maclist'] = [{'current':current_clients, \
            'peak':peak_maclist}]
        return result_dict

    def wireless_stats(self, **kwargs):
        '''SITES WITH DECREASE IN WIRELESS EXPERIENCES'''
        #logic to be inplemented
        result_dict = {} 
        result_dict["wifi_exp"] = {}
        result_dict["wifi_exp"]['message'] = \
            "SITES WITH DECREASE IN WIRELESS EXPERIENCES"
        result_dict["wifi_exp"]['count'] = 0 
        result_dict["wifi_exp"]['status'] = True
        if self.reporttype == 1:
            result_dict["wifi_exp"]['mac'] = []
        return result_dict['wifi_exp']


