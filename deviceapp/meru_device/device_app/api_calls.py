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
        request_dict ={}
        response = {}
        maclist = []
        for key in request.GET:

            request_dict[key] = ast.literal_eval(request.GET.get(key).strip()
                                 ) if request.GET.get(key) else 0
        if "time" not in request_dict:
                response = HttpResponse(json.dumps({"status": "false","message": "No time stamp specified"}))
        if "mac" not in request_dict:
                response = HttpResponse(json.dumps({"status": "false","message": "No mac specified"}))
        if not response and request_dict['time'][0] > request_dict['time'][1]:
                response = HttpResponse(json.dumps({"status": "false","message": "Wrong time range"}))
        if not response:
            if 'time' in request_dict and "mac" in request_dict and 'reportType' in request_dict:
                maclist = request_dict['mac']
                obj = HomeStats(maclist = maclist, gt=request_dict['time'][0],lt=request_dict['time'][1],reportType = request_dict['reportType'])
            elif 'time' in request_dict and "mac" in request_dict:
                # API for gathering detailed info about the home stats 1 on timestamp and MAC basis
                maclist = request_dict['mac']
                obj = HomeStats(maclist = maclist, gt=request_dict['time'][0],lt=request_dict['time'][1])
            
            # SITES WITH DECREASE IN WIRELESS EXPERIENCES#
            response_list.append(obj.wireless_stats())
            #------------------------
            # SITES WITH CHANGE IN SECURITY#
            response_list.append(obj.change_security())
            #------------------------
            # SITES WITH VERY HIGH ACCESS POINT UTILIZATION#
            response_list.append(obj.access_pt_util())
            #-------------------------
            # SITES WITH DEVICES DOWN#
            response_list.append(obj.sites_down())
            #--------------------------
            # SITES WITH CRITICAL HEALTH
            response_list.append(obj.sites_critical_health())
            #--------------------------
            # SITES WITH CRITICAL ALARMS#
            response_list.append(obj.critical_alarms())
            #----------------------------
            
            response = HttpResponse(json.dumps({"status": "true", \
             "values": response_list,\
             "message": "Home page API for pannel 1 stats"}))
        return response
        
class HomeApi2(View):

    ''' Home page API'''

    def get(self, request):
        ''' API calls initaited for home page'''
        response_list = []
        request_dict ={}
        response = {}
        maclist = []
        for key in request.GET:

            request_dict[key] = ast.literal_eval(request.GET.get(key).strip()
                                 ) if request.GET.get(key) else 0
        if "time" not in request_dict:
                response = HttpResponse(json.dumps({"status": "false","message": "No time stamp specified"}))
        if "mac" not in request_dict:
                response = HttpResponse(json.dumps({"status": "false","message": "No mac specified"}))
        if not response and request_dict['time'][0] > request_dict['time'][1]:
                response = HttpResponse(json.dumps({"status": "false","message": "Wrong time range"}))
        if not response:
            if 'time' in request_dict and "mac" in request_dict and 'reportType' in request_dict:
                maclist = request_dict['mac']
                obj = HomeStats(maclist = maclist, gt=request_dict['time'][0],lt=request_dict['time'][1],reportType = request_dict['reportType'])
            elif 'time' in request_dict and "mac" in request_dict:
                # API for gathering detailed info about the home stats 2 on timestamp and MAC basis
                maclist = request_dict['mac']
                obj = HomeStats(maclist = maclist, gt=request_dict['time'][0],lt=request_dict['time'][1])
            
            # WIRELESS CLIENTS
            response_list.append(obj.wireless_clients())
            # ACCESS POINTS
            response_list.append(obj.access_points())
            # ALARMS
            response_list.append(obj.alarms())
            # CONTROLLER UTILIZATION
            response_list.append(obj.controller_util())
            response = HttpResponse(json.dumps({"status": "true", \
             "values": response_list , \
             "message": "Home page API for pannel 2 stats"}))
        return response


class DashboardApi(View):

    ''' Dashboard status API'''

    def get(self, request):
        ''' API calls initaited for Dashboard Stats'''
        response_list = []
        request_dict ={}
        response = {}
        maclist = []
        for key in request.GET:

            request_dict[key] = ast.literal_eval(request.GET.get(key).strip()
                                 ) if request.GET.get(key) else 0
        if "time" not in request_dict:
                response = HttpResponse(json.dumps({"status": "false","message": "No time stamp specified"}))
        if "mac" not in request_dict:
                response = HttpResponse(json.dumps({"status": "false","message": "No mac specified"}))
        if not response and request_dict['time'][0] > request_dict['time'][1]:
                response = HttpResponse(json.dumps({"status": "false","message": "Wrong time range"}))
        if not response:
            if 'time' in request_dict and "mac" in request_dict and 'reportType' in request_dict:
                maclist = request_dict['mac']
                obj = DashboardStats(maclist = maclist, gt=request_dict['time'][0],lt=request_dict['time'][1],reportType = request_dict['reportType'])
            elif 'time' in request_dict and "mac" in request_dict:
                # API for gathering detailed info about the home stats 2 on timestamp and MAC basis
                maclist = request_dict['mac']
                obj = DashboardStats(maclist = maclist, gt=request_dict['time'][0],lt=request_dict['time'][1])
            
            # NUMBER OF CONTROLLERS #
            response_list.append(obj.number_controllers())

            # NUMBER OF STATIONS #
            response_list.append(obj.number_stations())

            # WI-FI EXPERIENCE #
            response_list.append(obj.wifi_exp())

            # NUMBER OF ONLINE OFFLINE APS #
            response_list.append(obj.online_offline_aps())

            # Status Since Last Login #
            response_list.append(obj.alarms_count())
                    
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
