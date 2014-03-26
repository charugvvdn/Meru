import json
from django.http import HttpResponse
from django.views.generic.base import View
from views import Common
import ast

try:
    from api import DashboardStats,HomeStats,OFFSET,UTC_1970,UTC_NOW,DB
except ImportError, e:
    print "api_calls.py"
    print e

class HomeApi(View):

    ''' Home page API'''

    def get(self, request):
        ''' API calls initaited for home page'''
        response_list = []
        response = {}
        home_stats = HomeStats()
        getlist = 0
        reporttype = ''
        if 'getlist' in request.GET:
            getlist = int(request.GET.get('getlist'))

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
                response = HttpResponse(json.dumps(\
                    {"status": "false","message": "No matching MAC data"}\
                    ))
        

        ''' spiliting the functions to separate APIs'''
        if 'reportType' in request.GET and home_stats.post_data['reportType'] and not response:

            reporttype = home_stats.post_data['reportType']
            res_list = []
            if reporttype == 'wirelessStats':
                res_list = home_stats.wireless_stats(p_data = \
                    home_stats.post_data,getlist = getlist)
                
            if reporttype == 'change_security':
                res_list = home_stats.change_security\
                (doc_list = doc_list,getlist = getlist)
            if reporttype == "access_pt_util":
                res_list = home_stats.access_pt_util\
                (doc_list = doc_list,p_data = \
                    home_stats.post_data,getlist = getlist)
            if reporttype == "sites_down":
                res_list = home_stats.sites_down \
                (doc_list = doc_list,getlist = getlist)
            if reporttype == "sites_critical_health":
                res_list = home_stats.sites_critical_health\
                (doc_list = doc_list,getlist = getlist)
            if reporttype == "sites_critical_alarms":
                res_list = home_stats.critical_alarms\
                (doc_list = doc_list,getlist = getlist)

            response = HttpResponse(json.dumps(\
                    {"status": "true","values":res_list,"message": reporttype}\
                    ))


        if not reporttype and not response:
            # SITES WITH DECREASE IN WIRELESS EXPERIENCES#
            response_list.append(
                home_stats.wireless_stats(p_data = \
                    home_stats.post_data,getlist = getlist))
            #------------------------
            # SITES WITH CHANGE IN SECURITY#
            response_list.append(home_stats.change_security\
                (doc_list = doc_list,getlist = getlist))
            #------------------------
            # SITES WITH VERY HIGH ACCESS POINT UTILIZATION#
            response_list.append(home_stats.access_pt_util\
                (doc_list = doc_list,p_data = \
                    home_stats.post_data,getlist = getlist))
            #-------------------------
            # SITES WITH DEVICES DOWN#
            response_list.append(home_stats.sites_down\
                (doc_list = doc_list,getlist = getlist))
            #--------------------------
            # SITES WITH CRITICAL HEALTH
            response_list.append(home_stats.sites_critical_health\
                (doc_list = doc_list,getlist = getlist))
            #--------------------------
            # SITES WITH CRITICAL ALARMS#
            response_list.append(home_stats.critical_alarms\
                (doc_list = doc_list,getlist = getlist))
            #----------------------------
            
            response = HttpResponse(json.dumps({"status": "true", \
             "values": response_list,\
             "message": "Home page API for pannel 1 stats"}))
        return response


class HomeApi2(View):

    ''' Home page API'''

    def get(self, request):
        ''' API calls initaited for home page'''
        home_stats = HomeStats()
        response_list = []
        doc_list = []
        response = {}
        start_time = 0
        end_time = 0
        getlist = 0
        reporttype = ''
        if 'getlist' in request.GET:
            getlist = int(request.GET.get('getlist'))
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
                response = HttpResponse(json.dumps(\
                    {"status": "false","message": "No matching MAC data"}\
                    ))
        ''' if timestamp not mentioned in query string,
             it takes last 30 minutes data'''
        time_frame = home_stats.post_data['time'] if 'time' \
        in home_stats.post_data else None
        start_time = time_frame[0] if time_frame else \
        int((OFFSET - UTC_1970).total_seconds())
        end_time = time_frame[1] if time_frame else \
        int((UTC_NOW - UTC_1970).total_seconds())
        
        ''' spiliting the functions to separate APIs'''
        if 'reportType' in request.GET and home_stats.post_data['reportType'] and not response:

            reporttype = home_stats.post_data['reportType']
            print reporttype
            res_list = []
            if reporttype == 'wireless_clients':
                res_list = home_stats.wireless_clients(mac_list = \
                    home_stats.post_data['mac']\
                    ,start_time = start_time, end_time = \
                    end_time, getlist = getlist )
                
            if reporttype == 'access_points':
                res_list = home_stats.access_points\
                (mac_list = home_stats.\
                post_data['mac'],start_time = start_time, \
                end_time = end_time,getlist = getlist)
            if reporttype == "alarms":
                res_list = home_stats.alarms\
                (doc_list = doc_list,getlist = getlist)
            if reporttype == "controller_util":
                res_list = home_stats.controller_util\
                (doc_list = doc_list)
            

            response = HttpResponse(json.dumps(\
                    {"status": "true","values":res_list,"message": reporttype}\
                    ))
        if not reporttype and not response:
            # WIRELESS CLIENTS
            response_list.append(
                home_stats.wireless_clients(mac_list = \
                    home_stats.post_data['mac']\
                    ,start_time = start_time, end_time = \
                    end_time, getlist = getlist ))
            # ACCESS POINTS
            response_list.append(home_stats.access_points\
                (mac_list = home_stats.\
                post_data['mac'],start_time = start_time, \
                end_time = end_time,getlist = getlist))
            # ALARMS
            response_list.append(home_stats.alarms\
                (doc_list = doc_list,getlist = getlist))
            # CONTROLLER UTILIZATION
            response_list.append(home_stats.controller_util\
                (doc_list = doc_list))
            response = HttpResponse(json.dumps({"status": "true", \
             "values": response_list , \
             "message": "Home page API for pannel 2 stats"}))
        return response


class DashboardApi(View):

    ''' Dashboard status API'''

    def get(self, request):
        ''' API calls initaited for Dashboard Stats'''
        response_list = []
        doc_list = []
        response = {}
        reporttype = ''
        dash_stats = DashboardStats()
        getlist = 0
        if 'getlist' in request.GET:
            getlist = int(request.GET.get('getlist'))
        for key in request.GET:
            dash_stats.post_data[key] = \
                ast.literal_eval(request.GET.get(key).strip()
                                 ) if request.GET.get(key) else 0
        if 'mac' not in dash_stats.post_data or not dash_stats.post_data['mac']:
            response = HttpResponse(json.dumps({"status": "false",
                                                "message": "No MAC data"}))
        
        mac_list = dash_stats.post_data['mac'] if not response else []
        # get all the documents with the matching mac irrespective of timestamp
        try:
            for mac in mac_list:
                cursor = DB.devices.find({"lower_snum":mac.lower() })\
                .sort('timestamp', -1).limit(1)
                for doc in cursor:
                    doc_list.append(doc)
        except Exception, e:
            print e

        ''' spiliting the functions to separate APIs'''
        if 'reportType' in request.GET and dash_stats.post_data['reportType'] and not response:

            reporttype = dash_stats.post_data['reportType']
            print reporttype
            res_list = []
            if reporttype == 'number_controllers':
                res_list = dash_stats.number_controllers\
                (doc_list = doc_list,getlist = getlist)
                
            if reporttype == 'number_stations':
                res_list = dash_stats.number_stations\
                (doc_list = doc_list,getlist = getlist)
            if reporttype == "wifi_exp":
                res_list = dash_stats.wifi_exp\
                (doc_list = doc_list)
            if reporttype == "number_aps":
                res_list = dash_stats.number_aps\
                (doc_list = doc_list,getlist = getlist)
            if reporttype == "online_offline_aps":
                res_list = dash_stats.online_offline_aps\
                (doc_list = doc_list,getlist = getlist)
            if reporttype == "status_last_login":
                res_list = dash_stats.status_last_login\
                (doc_list = doc_list,getlist = getlist)
            

            response = HttpResponse(json.dumps(\
                    {"status": "true","values":res_list,"message": reporttype}\
                    ))
        
        if not len(doc_list) and not response:
            response = HttpResponse(json.dumps(\
                    {"status": "false","message": "No matching MAC data"}\
                    ))
        if not reporttype and not response:

            # NUMBER OF CONTROLLERS #
            response_list.append(dash_stats.number_controllers\
                (doc_list = doc_list,getlist = getlist))

            # NUMBER OF STATIONS #
            response_list.append(dash_stats.number_stations\
                (doc_list = doc_list,getlist = getlist))

            # WI-FI EXPERIENCE #
            response_list.append(dash_stats.wifi_exp\
                (doc_list = doc_list))

            # NUMBER OF APS #
            response_list.append(dash_stats.number_aps\
                (doc_list = doc_list,getlist = getlist))

            # NUMBER OF ONLINE OFFLINE APS #
            response_list.append(dash_stats.online_offline_aps\
                (doc_list = doc_list,getlist = getlist))

            # Status Since Last Login #
            response_list.append(dash_stats.status_last_login\
                (doc_list = doc_list,getlist = getlist))
                    
            response = HttpResponse(json.dumps({"status": "true", \
             "values": response_list , \
             "message": "Dashboard page API for stats"}))
        return response


class AlarmsApi(View):

    ''' Alarms list API'''

    def get(self, request):
        ''' API calls initaited for Alarms list'''
        response_list = []
        response = {}
        doc_list = []
        common = Common()
        post_data = {}
        
        for key in request.GET:
            post_data[key] = ast.literal_eval(request.GET.get(key).strip()) \
                if request.GET.get(key) else 0

        if 'mac' not in post_data or not post_data['mac']:
            response = HttpResponse(json.dumps({"status": "false",
                                                "message": "No MAC data"}))
        else:
            doc_list = common.let_the_docs_out(post_data)
        

        if not len(doc_list) and not response:
            response = HttpResponse(json.dumps(\
                {"status": "false","message": "No matching MAC data"}\
                ))

        # LIST OF ALARMS #

        for doc in doc_list:
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
        return response
