from pymongo import MongoClient
import datetime
from views import Common
import pymongo

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

    def __init__(self):
        self.common = Common()
        self.post_data = {}
        self.mac_list = []
        self.doc_list = []
        self.response = []
        self.result_dict = {}

    def number_stations(self, **kwargs ):
        '''API calculating NUMBER OF STATIONS '''
        typeof = 'clients'
        online_count = 0
        critical_count = 0
        result_dict = {}
        online_clients = []
        critical_clients = []
        for doc in kwargs['doc_list']:
            
            if 'msgBody' in doc and 'controller' in doc['msgBody']:
                if typeof in doc['msgBody'].get('controller'):
                    # get clients
                    
                    clients = doc.get('msgBody').get('controller').get(typeof)
                    unique_clients = {}
                    
                    for client in clients:
                        if client["mac"] not in unique_clients:
                            unique_clients[client["mac"]] = 0
                            if client['state'].lower() == 'associated':
                                online_count += 1
                                online_clients.append(client['mac'])
                            else:
                                critical_count += 1
                                critical_clients.append(client['mac'])
        result_dict['label'] = 'Number of stations'
        result_dict['data'] = [online_count, critical_count]
        if kwargs['getlist'] == 1:
            result_dict['station_list'] = [online_clients, critical_clients]
        return result_dict

    def number_controllers(self, **kwargs ):
        '''API calculating NUMBER OF SITES '''
        typeof = 'controller'
        count = 0
        result_dict = {}
        maclist = []
        for doc in kwargs['doc_list']:
            if 'msgBody' in doc:
                if doc['msgBody'].get(typeof):
                    count += 1
                    maclist.append(doc['snum'])
                
        result_dict['label'] = 'Number of controllers'
        result_dict['data'] = [count]
        if kwargs['getlist'] == 1:
            result_dict['maclist'] = [maclist]
        return result_dict

    def wifi_exp(self, **kwargs):
        '''API calculating WI-FI EXPERIENCE '''
        typeof = 'clients'
        count = 0
        wifi_client = 0

        result_dict = {}

        for doc in kwargs['doc_list']:
            if 'msgBody' in doc and 'controller' in doc['msgBody']:
                if typeof in doc['msgBody'].get('controller'):
                    clients = doc.get('msgBody').get('controller').get(typeof)
                    for client in clients:
                        wifi_client += client['wifiExp']
                        count += 1

                    aps = doc.get('msgBody').get('controller').get('aps')
                    for ap in aps:
                        wifi_client += ap['wifiExp']
                        count += 1
        result_dict['label'] = 'Wifi experience'
        result_dict['data'] = [wifi_client / count] if count > 0 else [0]
        return result_dict

    def number_aps(self, **kwargs ):
        '''API calculating NUMBER OF APS '''
        typeof = 'aps'
        count = 0
        result_dict = {}
        aplist = []
        for doc in kwargs['doc_list']:
            if 'msgBody' in doc and 'controller' in doc['msgBody']:
                if typeof in doc['msgBody'].get('controller'):
                    # get the aps
                    aps = doc.get('msgBody').get('controller').get(typeof)
                    unique_aps = {}
                    for ap_elem in aps:
                        if ap_elem["mac"] in unique_aps:
                            unique_aps[ap_elem["mac"]] += 1
                        else:
                            unique_aps[ap_elem["mac"]] = 0
                            aplist.append(ap_elem['mac'])
                            count += 1
                        
        result_dict['label'] = 'Number of aps'
        result_dict['data'] = [count]
        if kwargs['getlist'] == 1:
            result_dict['aplist'] = [aplist]
        return result_dict

    def online_offline_aps(self, **kwargs ):
        '''API calculating NUMBER OF APS '''
        typeof = 'aps'
        online_count = 0
        offline_count = 0
        result_dict = {}
        online_aplist = []
        offline_aplist = []
        for doc in kwargs['doc_list']:
            if 'msgBody' in doc and 'controller' in doc['msgBody']:
                if typeof in doc['msgBody'].get('controller'):
                    # get the aps
                    aps = doc.get('msgBody').get('controller').get(typeof)
                    unique_aps = {}
                    for ap_elem in aps:
                        if ap_elem["mac"] not in unique_aps:
                            unique_aps[ap_elem["mac"]] = 0
                            if ap_elem['status'].lower() == 'up':
                                online_count += 1
                                online_aplist.append(ap_elem['mac'])
                            else:
                                offline_count += 1
                                offline_aplist.append(ap_elem['mac'])
        result_dict['label'] = 'Number of online offline aps'
        result_dict['data'] = [online_count, offline_count]
        if kwargs['getlist'] == 1:
            result_dict['aplist'] = [online_aplist, offline_aplist]
        return result_dict

    def status_last_login(self, **kwargs ):
        '''API calculating STATUS SINCE LAST LOGIN '''
        
        sites_count = 0
        controller_count = 0
        critical_alarm_count = 0
        result_dict = {}
        client_list = []
        controller_list = []
        critical_alarm_maclist = []
        for doc in kwargs['doc_list']:
            if 'msgBody' in doc and 'controller' in doc['msgBody']:
                if 'clients' in doc['msgBody'].get('controller'):
                    # get clients to count sites
                    clients = doc.get('msgBody').get(
                        'controller').get('clients')
                    
                    sites_count += len(clients)
                    for client in clients:
                        client_list.append(client['mac'])
                    
                if doc['msgBody'].get('controller'):
                    # get controller count
                    controller_count += 1
                    controller_list.append(doc['snum'])
                if 'alarms' in doc['msgBody'].get('controller'):
                    # get alarms to count critical alarms
                    alarms = doc.get('msgBody').get('controller').get('alarms')
                    for alarm in alarms:
                        if alarm['severity'].lower() == 'high':
                            critical_alarm_count += 1
                            critical_alarm_maclist.append(doc['snum'])
        result_dict['label'] = 'Status since last login'
        result_dict['data'] = [sites_count, controller_count,
                               critical_alarm_count]
        if kwargs['getlist'] == 1:
            result_dict['maclist'] = [{"clients":client_list, \
            "controller":controller_list,\
             "alarms":critical_alarm_maclist}]
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

    def access_pt_util(self, **kwargs):
        '''b. SITES WITH VERY HIGH ACCESS POINT UTILIZATION'''
        mac_list = []
        typeof = "aps"
        threshhold_max = 0
        if 'threshhold' in kwargs['p_data']:
            threshhold = kwargs['p_data']['threshhold']
            threshhold_max = threshhold[1]

        else:
            threshhold_max = int(78799)

        for doc in kwargs['doc_list']:
            mac = doc['snum']
            flag = 0
            rx_tx = 0
            if 'msgBody' in doc and 'controller' in doc['msgBody']:
                if typeof in doc['msgBody'].get('controller'):
                    # get the aps
                    aps = doc.get('msgBody').get('controller').get(typeof)
                    for ap_elem in aps:
                        # sum of rx + tx bytes
                        rx_tx = ap_elem['rxBytes'] + ap_elem['txBytes']
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
        if kwargs['getlist'] == 1:
            self.result_dict["access_pt"]['mac'] = mac_list
        return self.result_dict['access_pt']

    def change_security(self, **kwargs):
        ''' API Calculating change in security # '''
        mac_list = []
        
        ''' logic to be implemented'''

        self.result_dict["change_security"] = {}
        self.result_dict["change_security"]['message'] = \
            "SITES WITH CHANGE IN SECURITY"
        self.result_dict["change_security"]['count'] = 1
        self.result_dict["change_security"]['status'] = True
        if kwargs['getlist'] == 1 :
            self.result_dict["change_security"]['mac'] = mac_list
        return self.result_dict['change_security']

    def sites_critical_health(self, **kwargs):
        '''SITES WITH CRITICAL HEALTH'''
        mac_list = []
        typeof = "aps"
        for doc in kwargs['doc_list']:
            mac = doc['snum']
            flag = 0
            if 'msgBody' in doc and 'controller' in doc['msgBody']:
                if typeof in doc['msgBody'].get('controller'):
                    # get the access points
                    aps = doc.get('msgBody').get('controller').get(typeof)
                    for ap_elem in aps:
                        # mark the mac where ap is down
                        if ap_elem['status'].lower() == 'down':
                            flag = 1
                    if flag and mac not in mac_list:
                        mac_list.append(mac)
        self.result_dict["sites_critcal_health"] = {}
        self.result_dict["sites_critcal_health"]['message'] = \
            "SITES WITH CRITICAL HEALTH"
        self.result_dict["sites_critcal_health"]['count'] = len(mac_list)
        self.result_dict["sites_critcal_health"]['status'] = True
        if kwargs['getlist'] == 1:
            self.result_dict["sites_critcal_health"]['mac'] = mac_list
        return self.result_dict["sites_critcal_health"]

    def sites_down(self, **kwargs):
        '''b. SITES WITH DEVICES DOWN'''
        mac_list = []
        typeof = "aps"
        for doc in kwargs['doc_list']:
            mac = doc['snum']
            flag = 0
            if 'msgBody' in doc and 'controller' in doc['msgBody']:
                if typeof in doc['msgBody'].get('controller'):
                    aps = doc.get('msgBody').get('controller').get(typeof)
                    for ap_elem in aps:
                        # mark the mac where ap is down
                        if ap_elem['status'].lower() == 'down':
                            flag = 1
                    if flag and mac not in mac_list:
                        mac_list.append(mac)
        self.result_dict["sites_down"] = {}
        self.result_dict["sites_down"]['message'] = "SITES WITH DEVICES DOWN"
        self.result_dict["sites_down"]['count'] = len(mac_list)
        self.result_dict["sites_down"]['status'] = True
        if kwargs['getlist'] == 1 :
            self.result_dict["sites_down"]['mac'] = mac_list
        return self.result_dict["sites_down"]

    def critical_alarms(self, **kwargs):
        '''SITES WITH CRITICAL ALARMS'''
        mac_list = []
        typeof = "alarms"
        for doc in kwargs['doc_list']:
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
        if kwargs['getlist'] == 1:
            self.result_dict["critical_alarm"]['mac'] = mac_list
        return self.result_dict["critical_alarm"]

    def controller_util(self, **kwargs ):
        '''API calculating controller utilization count'''
        typeof = 'controller'
        gt_50_count = 10
        _50_75_count = 20
        lt_75_count = 33
        result_dict = {}

        for doc in kwargs['doc_list']:
            if 'msgBody' in doc and 'controller' in doc['msgBody']:
                if typeof in doc['msgBody'].get('controller'):
                    '''controllers = doc.get('msgBody').get('controller')\
                    .get(typeof)
                    # logic to be implemented'''
        result_dict['label'] = 'Controller Utilization'
        result_dict['data'] = [gt_50_count, _50_75_count, lt_75_count]
        return result_dict

    def alarms(self, **kwargs ):
        '''API calculating critical, high, minor alarms'''
        typeof = 'alarms'
        critical_count = 0
        high_count = 0
        minor_count = 0
        result_dict = {}
        high_alarm = []
        critical_alarm = []
        minor_alarm  = []
        for doc in kwargs['doc_list']:
            if 'msgBody' in doc and 'controller' in doc['msgBody']:
                if typeof in doc['msgBody'].get('controller'):
                    alarms = doc.get('msgBody').get('controller').get(typeof)
                    for alarm in alarms:
                        if alarm['severity'].lower() == 'high':
                            high_count += 1
                            high_alarm.append(doc['snum'])
                        elif alarm['severity'].lower() == 'critical':
                            critical_count += 1
                            critical_alarm.append(doc['snum'])
                        elif alarm['severity'].lower() == 'low':
                            minor_count += 1
                            minor_alarm.append(doc['snum'])
        result_dict['label'] = 'Alarms'
        result_dict['data'] = [critical_count, high_count, minor_count]
        if kwargs['getlist'] == 1:
            result_dict['maclist'] = [{"critical":critical_alarm, \
             "high":high_alarm, "minor":minor_alarm}]
        return result_dict

    def access_points(self, **kwargs):
        ''' API Calculating online, offline, down aps # '''
        typeof = 'aps'
        online_count = 0
        offline_count = 0
        down_aps = 0
        result_dict = {}
        unique_ap = {}
        offline_maclist = []
        online_maclist = []
        for mac in kwargs['mac_list']:

            cursor = DB.devices.find({"lower_snum": mac.lower() , "timestamp":\
             {"$gt": kwargs['start_time'], "$lt": kwargs['end_time']}})\
            .sort('timestamp', -1)

        
            for doc in cursor:
        
                if 'msgBody' in doc and 'controller' in doc['msgBody']:
                    if typeof in doc['msgBody'].get('controller'):
                        aps = doc.get('msgBody').get('controller').get(typeof)
                        
                        for ap_elem in aps:
                            if ap_elem["mac"] in unique_ap:
                                pass
                            else:
                                unique_ap[ap_elem["mac"]] = 0
                                if ap_elem['status'].lower() == 'down':
                                    offline_count += 1
                                    offline_maclist.append(ap_elem['mac'])
                                else:
                                    online_count += 1
                                    online_maclist.append(ap_elem['mac'])

        result_dict['label'] = 'Access point'
        result_dict['data'] = [online_count, offline_count, down_aps]
        if kwargs['getlist'] == 1:
            result_dict['maclist'] = [{"online":online_maclist, \
             "offline":offline_maclist, "down":[]}]
        return result_dict

    def wireless_clients(self, **kwargs):
        ''' API Calculating wireless clients count according to timestamp '''
        typeof = 'clients'
        time_list = []
        result_list = []
        result_dict = {}
        unique_clients = {}
        result_dict['mac']  = {}
        time_list = []
        
        # query over mongo DB to get the data between the given timestamp in
        # desc

        cursor = DB.devices.find({"timestamp": {"$gt": kwargs['start_time'] , \
         "$lt": kwargs['end_time']}}).sort('timestamp', -1)
        
        mac_list = [x.lower() for x in kwargs['mac_list']]
        result_list = []
        result_maclist = []
        result_dict = {}
        
        
        for elem in cursor:
            if elem['timestamp'] not in time_list:
                time_list.append(elem['timestamp']) 
        for time in time_list:
            cursor = DB.devices.find({"timestamp": time})
            
            count = 0
            unique_clients = {}
            for doc in cursor:
                
                if  doc['lower_snum'] in mac_list:
                    
                    # count the clients in each document at a single timestamp
                    # and matching mac
                    if 'msgBody' in doc and 'controller' in doc['msgBody']:
                        if typeof in doc['msgBody'].get('controller'):
                            clients = doc.get('msgBody').get('controller').\
                                get(typeof)
                            
                            for client in clients:
                                if client['mac'] not in unique_clients:
                                    unique_clients[client['mac']] = 0
                                    count += 1
            result_list.append(count)
            if kwargs['getlist'] == 1:
                mac_dict = {}
                mac_dict ['list'] = [key for key in unique_clients]
                mac_dict['count'] = count
                print mac_dict
                result_maclist.append(mac_dict)
        print result_maclist
        # count of clients currently (near or at last timestamp)
        current = result_list[0] if result_list else 0
        # max count of clients among count of clients at every timestamp
        peak = max(result_list) if result_list else 0
        # average count of clients at every timestamp
        avg = reduce(lambda x, y: x + y, result_list) / \
            len(result_list) if len(result_list) > 0 else 0
        result_dict['label'] = 'Wireless Clients'
        result_dict['data'] = [current, peak, avg]
        if kwargs['getlist'] and len(result_maclist) > 0:
            current_maclist = result_maclist[0]['list']
            peak_mac_list = max(result_maclist, key=lambda x:x['count'])
            peak_maclist = peak_mac_list['list']

            result_dict['maclist'] = [{'current':current_maclist, \
            'peak':peak_maclist}]
        return result_dict

    def wireless_stats(self, **kwargs):
        '''SITES WITH DECREASE IN WIRELESS EXPERIENCES'''
        wifiexp_ap_sum = 0
        typeof = "aps"
        aps_count = len_controller_list = 0
        avg_doc_wifiexp = 0
        avg_controller = 0
        final_avg_controller = 0
        doc_list = []
        flag = 0
        controller_list = []
        mac_list = kwargs['p_data']['mac']
        time_frame = kwargs['p_data']['time'] if 'time' in \
        kwargs['p_data'] else None
        start_time = time_frame[0] if time_frame else \
        int((OFFSET - UTC_1970).total_seconds())
        end_time = time_frame[1] if time_frame else \
        int((UTC_NOW - UTC_1970).total_seconds())
        
        for mac in mac_list:

            doc_list = []
            # filter over given mac and timestamp (in query string)
            cursor = DB.devices.find({"lower_snum": mac.lower(), "timestamp" \
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
                        for ap_elem in aps:
                            # sum of wifi of aps
                            wifiexp_ap_sum += int(ap_elem['wifiExp'])
                            aps_count += 1  # number of aps

                        # average of wifi aps in a doc
                        avg_doc_wifiexp = wifiexp_ap_sum / aps_count \
                        if aps_count > 0 else 0
                        # sum of avergae of wifi of aps in all the docs
                        avg_controller += avg_doc_wifiexp
            # average of avergae of wifi of aps in all the docs
            final_avg_controller = avg_controller / len(doc_list) if \
            len(doc_list) > 0 else 0
            last_doc = doc_list[0].get('msgBody').get('controller').\
            get(typeof) or []
            flag = 0
            for ap_elem in last_doc:
                # mark the mac where ap wifiexp - final average of all wifi is
                # < 0
                if int(ap_elem['wifiExp']) - final_avg_controller < 0:
                    flag = 1
            if flag:
                len_controller_list += 1

            if kwargs['getlist'] == 1:
                controller_list.append(doc_list[0]['snum'])

        self.result_dict["wifi_exp"] = {}
        self.result_dict["wifi_exp"]['message'] = \
            "SITES WITH DECREASE IN WIRELESS EXPERIENCES"
        self.result_dict["wifi_exp"]['count'] = len_controller_list
        self.result_dict["wifi_exp"]['status'] = True
        if kwargs['getlist'] == 1:
            self.result_dict["wifi_exp"]['mac'] = controller_list
        return self.result_dict['wifi_exp']


