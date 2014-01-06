from django.http import HttpResponse, StreamingHttpResponse
from pymongo import MongoClient
import datetime
import json
from django.views.generic.base import View
from views import Common
import ast
# Connection with mongodb client
client = MongoClient()
db = client['nms']

def add_header(result) :
    result["Access-Control-Allow-Origin"] = "*"
    result['Content-Type'] = 'application/json'
    result["Access-Control-Allow-Methods"] = "GET, OPTIONS"
    result["Access-Control-Max-Age"] = "1000"
    result["Access-Control-Allow-Headers"] = "*"
    return result

class DashboardStats():

    '''Common variable used under the class methods'''

    def __init__(self):
        self.common = Common()
        self.post_data = {}
        self.mac_list = []
        self.doc_list = []
        self.response = []
        self.result_dict = {}

    def number_stations(self, doc_list, typeof='clients'):
        '''API calculating NUMBER OF SITES '''
        online_count = 0
        critical_count = 0
        result_dict = {}
        for doc in doc_list:
            
            if 'msgBody' in doc and 'controller' in doc['msgBody']:
                if typeof in doc['msgBody'].get('controller'):
                    # get clients
                    
                    clients = doc.get('msgBody').get('controller').get(typeof)
                    print clients
                    for client in clients:
                        if client['state'].lower() == 'associated':
                            online_count += 1
                        else:
                            critical_count += 1
        result_dict['label'] = 'Number of stations'
        result_dict['data'] = [online_count, critical_count]
        return result_dict

    def number_controllers(self, doc_list, typeof='controller'):
        '''API calculating NUMBER OF STATIONS '''
        count = 0
        result_dict = {}

        for doc in doc_list:
            if 'msgBody' in doc:
                if doc['msgBody'].get(typeof):
                # get controller
                    controller = doc.get('msgBody').get(typeof)
                    count += 1
        result_dict['label'] = 'Number of controllers'
        result_dict['data'] = [count]
        return result_dict

    def wifi_exp(self, doc_list, typeof='clients'):
        '''API calculating WI-FI EXPERIENCE '''
        count = 0
        wifi_client = 0

        result_dict = {}

        for doc in doc_list:
            if 'msgBody' in doc and 'controller' in doc['msgBody']:
                if typeof in doc['msgBody'].get('controller'):
                    clients = doc.get('msgBody').get('controller').get(typeof)
                    for client in clients:
                        wifi_client += client['wifiExp']
                        count += 1
        result_dict['label'] = 'Wifi experience'
        result_dict['data'] = [wifi_client / count] if count > 0 else [0]
        return result_dict

    def number_aps(self, doc_list, typeof='aps'):
        '''API calculating NUMBER OF APS '''
        count = 0
        result_dict = {}

        for doc in doc_list:
            if 'msgBody' in doc and 'controller' in doc['msgBody']:
                if typeof in doc['msgBody'].get('controller'):
                    # get the aps
                    aps = doc.get('msgBody').get('controller').get(typeof)
                    unique_aps = {}
                    for ap in aps:
                        if ap["mac"] in unique_aps:
                            unique_aps[ap["mac"]] += 1
                        else:
                            unique_aps[ap["mac"]] = 0
                            count += 1
                        
        result_dict['label'] = 'Number of aps'
        result_dict['data'] = [count]
        return result_dict

    def online_offline_aps(self, doc_list, typeof='aps'):
        '''API calculating NUMBER OF APS '''
        online_count = 0
        offline_count = 0
        result_dict = {}

        for doc in doc_list:
            if 'msgBody' in doc and 'controller' in doc['msgBody']:
                if typeof in doc['msgBody'].get('controller'):
                    # get the aps
                    aps = doc.get('msgBody').get('controller').get(typeof)
                    for ap in aps:
                        if ap['status'].lower() == 'up':
                            online_count += 1
                        else:
                            offline_count += 1
        result_dict['label'] = 'Number of online offline aps'
        result_dict['data'] = [online_count, offline_count]
        return result_dict

    def status_last_login(self, doc_list, typeof='controller'):
        '''API calculating STATUS SINCE LAST LOGIN '''
        sites_count = 0
        controller_count = 0
        critical_alarm_count = 0
        result_dict = {}

        for doc in doc_list:
            if 'msgBody' in doc and 'controller' in doc['msgBody']:
                if 'clients' in doc['msgBody'].get('controller'):
                    # get clients to count sites
                    clients = doc.get('msgBody').get(
                        'controller').get('clients')
                    for client in clients:
                        sites_count += 1
                if doc['msgBody'].get('controller'):
                    # get controller count
                    controller_count += 1
                if 'alarms' in doc['msgBody'].get('controller'):
                    # get alarms to count critical alarms
                    alarms = doc.get('msgBody').get('controller').get('alarms')
                    for alarm in alarms:
                        if alarm['severity'].lower() == 'high':
                            critical_alarm_count += 1
        result_dict['label'] = 'Status since last login'
        result_dict['data'] = [sites_count, controller_count,
                               critical_alarm_count]
        return result_dict


class HomeStats():

    '''Common variable used under the class methods'''

    def __init__(self):
        self.common = Common()
        self.post_data = {}
        self.mac_list = []
        self.doc_list = []
        self.response = []
        self.result_dict = {}

    def access_pt_util(self, doc_list, p_data, typeof="aps"):
        '''b. SITES WITH VERY HIGH ACCESS POINT UTILIZATION'''
        mac_list = []
        threshhold_max = 0
        if 'threshhold' in p_data:
            threshhold = p_data['threshhold']
            threshhold_max = threshhold[1]

        else:
            threshhold_max = int(78799)

        for doc in doc_list:
            mac = doc['snum']
            flag = 0
            rx_tx = 0
            if 'msgBody' in doc and 'controller' in doc['msgBody']:
                if typeof in doc['msgBody'].get('controller'):
                    # get the aps
                    aps = doc.get('msgBody').get('controller').get(typeof)
                    for ap in aps:
                        # sum of rx + tx bytes
                        rx_tx = ap['rxBytes'] + ap['txBytes']
                        # mark the mac where sum of rx+tx bytes is > threshold
                        if rx_tx > threshhold_max:
                            flag = 1
                    if flag and mac not in mac_list:
                        mac_list.append(mac)
        self.result_dict["access_pt"] = {}
        self.result_dict["access_pt"]['message'] = \
            "SITES WITH VERY HIGH ACCESS POINT UTILIZATION"
        self.result_dict["access_pt"]['count'] = len(mac_list)
        self.result_dict["access_pt"]['status'] = True
        self.result_dict["access_pt"]['mac'] = mac_list
        return self.result_dict['access_pt']

    def change_security(self, doc_list, typeof='aps'):
        ''' API Calculating change in security # '''
        count = 10
        mac_list = []

        ''' logic to be implemented'''

        self.result_dict["change_security"] = {}
        self.result_dict["change_security"]['message'] = \
            "SITES WITH CHANGE IN SECURITY"
        self.result_dict["change_security"]['count'] = 1
        self.result_dict["change_security"]['status'] = True
        self.result_dict["change_security"]['mac'] = mac_list
        return self.result_dict['change_security']

    def sites_critical_health(self, doc_list, typeof="aps"):
        '''SITES WITH CRITICAL HEALTH'''
        mac_list = []
        for doc in doc_list:
            mac = doc['snum']
            flag = 0
            if 'msgBody' in doc and 'controller' in doc['msgBody']:
                if typeof in doc['msgBody'].get('controller'):
                    # get the access points
                    aps = doc.get('msgBody').get('controller').get(typeof)
                    for ap in aps:
                        # mark the mac where ap is down
                        if ap['status'].lower() == 'down':
                            flag = 1
                    if flag and mac not in mac_list:
                        mac_list.append(mac)
        self.result_dict["sites_critcal_health"] = {}
        self.result_dict["sites_critcal_health"]['message'] = \
            "SITES WITH CRITICAL HEALTH"
        self.result_dict["sites_critcal_health"]['count'] = len(mac_list)
        self.result_dict["sites_critcal_health"]['status'] = True
        self.result_dict["sites_critcal_health"]['mac'] = mac_list
        return self.result_dict["sites_critcal_health"]

    def sites_down(self, doc_list, typeof="aps"):
        '''b. SITES WITH DEVICES DOWN'''
        mac_list = []
        for doc in doc_list:
            mac = doc['snum']
            flag = 0
            if 'msgBody' in doc and 'controller' in doc['msgBody']:
                if typeof in doc['msgBody'].get('controller'):
                    aps = doc.get('msgBody').get('controller').get(typeof)
                    for ap in aps:
                        # mark the mac where ap is down
                        if ap['status'].lower() == 'down':
                            flag = 1
                    if flag and mac not in mac_list:
                        mac_list.append(mac)
        self.result_dict["sites_down"] = {}
        self.result_dict["sites_down"]['message'] = "SITES WITH DEVICES DOWN"
        self.result_dict["sites_down"]['count'] = len(mac_list)
        self.result_dict["sites_down"]['status'] = True
        self.result_dict["sites_down"]['mac'] = mac_list
        return self.result_dict["sites_down"]

    def critical_alarms(self, doc_list, typeof="alarms"):
        '''SITES WITH CRITICAL ALARMS'''
        mac_list = []
        for doc in doc_list:
            mac = doc['snum']
            flag = 0
            if 'msgBody' in doc and 'controller' in doc['msgBody']:
                if typeof in doc['msgBody'].get('controller'):
                    alarms = doc.get('msgBody').get('controller').get(typeof)
                    for alarm in alarms:
                        # mark the mac where alarms severity is high
                        if alarm['severity'].lower() == 'high':
                            flag = 1
                    if flag and mac not in mac_list:
                        mac_list.append(mac)
        self.result_dict["critical_alarm"] = {}
        self.result_dict["critical_alarm"]['message'] = \
            "SITES WITH CRITICAL ALARMS"
        self.result_dict["critical_alarm"]['count'] = len(mac_list)
        self.result_dict["critical_alarm"]['status'] = True
        self.result_dict["critical_alarm"]['mac'] = mac_list
        return self.result_dict["critical_alarm"]

    def controller_util(self, doc_list, typeof='controller'):
        '''API calculating controller utilization count'''
        gt_50_count = 10
        _50_75_count = 20
        lt_75_count = 33
        result_dict = {}

        for doc in doc_list:
            if 'msgBody' in doc and 'controller' in doc['msgBody']:
                if typeof in doc['msgBody'].get('controller'):
                    controllers = doc.get('msgBody').get('controller').get(typeof)
                    '''for controller in controllers:
                        pass
                        # logic to be implemented'''
        result_dict['label'] = 'Controller Utilization'
        result_dict['data'] = [gt_50_count, _50_75_count, lt_75_count]
        return result_dict

    def alarms(self, doc_list, typeof='alarms'):
        '''API calculating critical, high, minor alarms'''
        critical_count = 0
        high_count = 0
        minor_count = 0
        result_dict = {}

        for doc in doc_list:
            if 'msgBody' in doc and 'controller' in doc['msgBody']:
                if typeof in doc['msgBody'].get('controller'):
                    alarms = doc.get('msgBody').get('controller').get(typeof)
                    for alarm in alarms:
                        if alarm['severity'].lower() == 'high':
                            high_count += 1
                        elif alarm['severity'].lower() == 'critical':
                            critical_count += 1
                        elif alarm['severity'].lower() == 'minor':
                            minor_count += 1
        result_dict['label'] = 'Alarms'
        result_dict['data'] = [critical_count, high_count, minor_count]
        return result_dict

    def access_points(self, doc_list, typeof='aps'):
        ''' API Calculating online, offline, down aps # '''
        online_count = 0
        offline_count = 0
        down_aps = 0
        result_dict = {}
        unique_ap = {}

        for doc in doc_list:
            if 'msgBody' in doc and 'controller' in doc['msgBody']:
                if typeof in doc['msgBody'].get('controller'):
                    aps = doc.get('msgBody').get('controller').get(typeof)
                    
                    for ap in aps:
                        if ap["mac"] in unique_ap:
                            pass
                        else:
                            unique_ap[ap["mac"]] = 0
                            if ap['status'].lower() == 'down':
                                down_aps += 1
                                offline_count += 1
                            else:
                                online_count += 1

        result_dict['label'] = 'Access point'
        result_dict['data'] = [online_count, offline_count, down_aps]
        return result_dict

    def wireless_clients(self, p_data, typeof='clients'):
        ''' API Calculating wireless clients count according to timestamp '''
        mac_list = p_data['mac']
        time_list = []

        if 'time' in p_data:
            ''' timestamp as mentioned in query string'''
            time_frame = p_data['time']
            start_time = time_frame[0]
            end_time = time_frame[1]

        else:
            ''' if timestamp not mentioned in query string,
             it takes last 30 minutes data'''
            utc_1970 = datetime.datetime(1970, 1, 1)
            utc_now = datetime.datetime.utcnow()
            offset = utc_now - datetime.timedelta(minutes=30)
            start_time = int((offset - utc_1970).total_seconds())
            end_time = int((utc_now - utc_1970).total_seconds())

        # query over mongo db to get the data between the given timestamp in
        # desc
        cursor = db.devices.find({"timestamp": {
                                 "$gt": start_time, "$lt": end_time}}).sort('timestamp', -1)

        result_list = []
        result_dict = {}
        for doc in cursor:
            # creating a list of timestamps found in 'cursor'
            if doc['timestamp'] not in time_list:
                time_list.append(doc['timestamp'])

        for time in time_list:
            count = 0
            for mac in mac_list:
                # under each timestamp in the list , filter the mac 
                cursor = db.devices.find({"lower_snum": mac.lower(), "timestamp" :time})
                for doc in cursor:
                    # count the clients in each document at a single timestamp
                    # and matching mac
                    if 'msgBody' in doc and 'controller' in doc['msgBody']:
                        if typeof in doc['msgBody'].get('controller'):
                            clients = doc.get('msgBody').get('controller').\
                                get(typeof)
                            for client in clients:
                                count += 1
            result_list.append(count)
        # count of clients currently (near or at last timestamp)
        current = result_list[0] if result_list else 0
        # max count of clients among count of clients at every timestamp
        peak = max(result_list) if result_list else 0
        # average count of clients at every timestamp
        avg = reduce(lambda x, y: x + y, result_list) / \
            len(result_list) if result_list else 0
        result_dict['label'] = 'Wireless Clients'
        result_dict['data'] = [current, peak, avg]
        return result_dict

    def wireless_stats(self, p_data, typeof="aps"):
        '''SITES WITH DECREASE IN WIRELESS EXPERIENCES'''
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
            # filter over given mac and timestamp (in query string)
            cursor = db.devices.find({"lower_snum": mac.lower(), "timestamp" \
                : {"$gt": start_time, "$lt": end_time}}).sort('timestamp',-1)
            res = cursor.count()
            if res == 0:
                continue
            avg_controller = 0
            for doc in cursor:
                doc_list.append(doc)

            for doc in doc_list:

                wifiexp_ap_sum = 0
                aps_count = 0
                # get the aps
                if 'msgBody' in doc and 'controller' in doc['msgBody']:
                    if typeof in doc['msgBody'].get('controller'):
                        aps = doc.get('msgBody').get('controller').get(typeof)
                        for ap in aps:
                            # sum of wifi of aps
                            wifiexp_ap_sum += int(ap['wifiExp'])
                            aps_count += 1  # number of aps

                        # average of wifi aps in a doc
                        avg_doc_wifiexp = wifiexp_ap_sum / aps_count if aps_count > 0 else 0
                        # sum of avergae of wifi of aps in all the docs
                        avg_controller += avg_doc_wifiexp
            # average of avergae of wifi of aps in all the docs
            final_avg_controller = avg_controller / len(doc_list) if len(doc_list) > 0 else 0
            last_doc = doc_list[0].get('msgBody').get('controller').get(typeof)
            flag = 0
            for ap in last_doc:
                # mark the mac where ap wifiexp - final average of all wifi is
                # < 0
                if int(ap['wifiExp']) - final_avg_controller < 0:
                    flag = 1
            if flag:
                controller_list.append(doc_list[0]['snum'])

        self.result_dict["wifi_exp"] = {}
        self.result_dict["wifi_exp"]['message'] = \
            "SITES WITH DECREASE IN WIRELESS EXPERIENCES"
        self.result_dict["wifi_exp"]['count'] = len(controller_list)
        self.result_dict["wifi_exp"]['status'] = True
        self.result_dict["wifi_exp"]['mac'] = controller_list
        return self.result_dict['wifi_exp']


class HomeApi(View):

    ''' Home page API'''

    def get(self, request):
        ''' API calls initaited for home page'''
        response_list = []
        response = {}
        home_stats = HomeStats()

        for key in request.GET:
            home_stats.post_data[key] = \
                ast.literal_eval(request.GET.get(key).strip()
                                 ) if request.GET.get(key) else 0

        if 'mac' not in home_stats.post_data or not home_stats.post_data['mac']:
            response = HttpResponse(json.dumps({"status": "false",
                                                "message": "No MAC data"}))
        else:
            # fetch the docs
            doc_list = home_stats.common.let_the_docs_out(home_stats.post_data)
            if not len(doc_list):
                response = HttpResponse(json.dumps({"status": "false",
                                                    "message": "No matching MAC data"}))

        if not response:
            # SITES WITH DECREASE IN WIRELESS EXPERIENCES#
            response_list.append(
                home_stats.wireless_stats(home_stats.post_data))
            #------------------------
            # SITES WITH CHANGE IN SECURITY#
            response_list.append(home_stats.change_security(doc_list))
            #------------------------
            # SITES WITH VERY HIGH ACCESS POINT UTILIZATION#
            response_list.append(home_stats.access_pt_util(doc_list,
                                                           home_stats.post_data))
            #-------------------------
            # SITES WITH DEVICES DOWN#
            response_list.append(home_stats.sites_down(doc_list))
            #--------------------------
            # SITES WITH CRITICAL HEALTH
            response_list.append(home_stats.sites_critical_health(doc_list))
            #--------------------------
            # SITES WITH CRITICAL ALARMS#
            response_list.append(home_stats.critical_alarms(doc_list))
            #----------------------------
            
            response = HttpResponse(json.dumps({"status": "true", \
             "values": response_list,\
             "message": "Home page API for pannel 1 stats"}))
        response = add_header(response)
        return response


class HomeApi2(View):

    ''' Home page API'''

    def get(self, request):
        ''' API calls initaited for home page'''
        home_stats = HomeStats()
        response_list = []
        doc_list = []
        response = {}
        for key in request.GET:
            home_stats.post_data[key] = \
                ast.literal_eval(request.GET.get(key).strip()
                                 ) if request.GET.get(key) else 0

        if 'mac' not in home_stats.post_data or not home_stats.post_data['mac']:
            response = HttpResponse(json.dumps({"status": "false",
                                                "message": "No MAC data"}))
        else:
            # fetch the docs
            doc_list = home_stats.common.let_the_docs_out(home_stats.post_data)
            if not len(doc_list):
                response = HttpResponse(json.dumps({"status": "false",
                                                    "message": "No matching MAC data"}))
        if not response:
            # WIRELESS CLIENTS
            response_list.append(
                home_stats.wireless_clients(home_stats.post_data))
            # ACCESS POINTS
            response_list.append(home_stats.access_points(doc_list))
            # ALARMS
            response_list.append(home_stats.alarms(doc_list))
            # CONTROLLER UTILIZATION
            response_list.append(home_stats.controller_util(doc_list))
            response = HttpResponse(json.dumps({"status": "true", \
             "values": response_list , \
             "message": "Home page API for pannel 2 stats"}))
        response = add_header(response)
        return response


class DashboardApi(View):

    ''' Dashboard status API'''

    def get(self, request):
        ''' API calls initaited for Dashboard Stats'''
        response_list = []
        doc_list = []
        all_doc_list = []
        response = {}
        dash_stats = DashboardStats()

        for key in request.GET:
            dash_stats.post_data[key] = \
                ast.literal_eval(request.GET.get(key).strip()
                                 ) if request.GET.get(key) else 0
        if 'mac' not in dash_stats.post_data or not dash_stats.post_data['mac']:
            response = HttpResponse(json.dumps({"status": "false",
                                                "message": "No MAC data"}))
        else:
            # fetch the docs
            doc_list = dash_stats.common.let_the_docs_out(dash_stats.post_data)

        mac_list = dash_stats.post_data['mac'] if not response else []
        # get all the documents with the matching mac irrespective of timestamp
        for mac in mac_list:
            cursor = db.devices.find({"lower_snum":mac.lower() })
            for doc in cursor:
                all_doc_list.append(doc)

        if not len(doc_list) and not len(all_doc_list) and not response:
                response = HttpResponse(json.dumps({"status": "false",
                                                    "message": "No matching MAC data"}))
        

                
        # NUMBER OF CONTROLLERS #
        response_list.append(dash_stats.number_controllers(all_doc_list))

        # NUMBER OF STATIONS #
        response_list.append(dash_stats.number_stations(all_doc_list))

        # WI-FI EXPERIENCE #
        response_list.append(dash_stats.wifi_exp(all_doc_list))

        # NUMBER OF APS #
        response_list.append(dash_stats.number_aps(all_doc_list))

        # NUMBER OF ONLINE OFFLINE APS #
        response_list.append(dash_stats.online_offline_aps(all_doc_list))

        # Status Since Last Login #
        response_list.append(dash_stats.status_last_login(doc_list))
        if not response:
        
            response = HttpResponse(json.dumps({"status": "true", \
             "values": response_list , \
             "message": "Dashboard page API for stats"}))
        response = add_header(response)
        return response


class AlarmsApi(View):

    ''' Alarms list API'''

    def get(self, request):
        ''' API calls initaited for Alarms list'''
        response_list = []
        response = {}
        doc_list = []
        all_doc_list = []
        post_data = {}

        for key in request.GET:
            post_data[key] = ast.literal_eval(request.GET.get(key).strip()) \
                if request.GET.get(key) else 0

        if 'mac' not in post_data or not post_data['mac']:
            response = HttpResponse(json.dumps({"status": "false",
                                                "message": "No MAC data"}))

        mac_list = post_data['mac'] if not response else []
        for mac in mac_list:
            cursor = db.devices.find({"lower_snum":mac.lower() })
            for doc in cursor:
                all_doc_list.append(doc)

        if not len(doc_list) and not len(all_doc_list) and not response:
                response = HttpResponse(json.dumps({"status": "false",
                                                    "message": "No matching MAC data"}))

        # LIST OF ALARMS #

        for doc in all_doc_list:
            if 'msgBody' in doc and 'controller' in doc['msgBody']:
                if 'alarms' in doc['msgBody'].get('controller'):
                    alarms = doc.get('msgBody').get(
                        'controller').get('alarms')
                    if alarms:
                        for alarm in alarms:
                            alarm['mac'] = doc['snum']
                            response_list.append(alarm)
        if not response:
            response = HttpResponse(json.dumps({"status": "true", \
             "values": response_list , \
             "message": "Alarms page API for alarms list"}))
        response = add_header(response)
        return response
