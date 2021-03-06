from django.http import HttpResponse, HttpResponseServerError
from django.db import connections, transaction
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q
import MySQLdb as mydb
from django import db
import pymongo
from pymongo import MongoClient
from django.shortcuts import render, render_to_response
from django.template import RequestContext
import datetime
import itertools
from collections import Counter, OrderedDict
import ast
import re
import json
import requests
from meru_device import settings
from device_app.models import controller, command, alarm, dashboard_info, \
    ssid, security_profile, ssid_in_command
from django.views.generic.base import View
TIME_INDEX = 60

# Connection with mongoDB client
DB = settings.DB
class Raw_Model():

    """
    Raw SQL queries methods
    """

    def isConfigData(self, mac,command_id):
        """
        Generating the commands for the controller with
        given controller mac address passed as `mac`
        :param mac:
        """

        cursor = connections['meru_cnms_sitegroup'].cursor()


        command_query = """SELECT command_json, command_id FROM meru_command WHERE \
        `command_mac` = '%s' AND `command_id` > %s LIMIT 1""" % (mac,command_id)

	count_query = """SELECT COUNT(*) FROM meru_command WHERE \
	`command_mac` = '%s' AND `command_id` > %s""" % (mac, command_id)

	print "mysql access in isConfig"
	print datetime.datetime.now()
        cursor.execute(command_query)
	print "process complete"
	print datetime.datetime.now()
        result = cursor.fetchall()

        if result:
	    cursor.execute(count_query)
	    command_count = cursor.fetchall()
            new_command_id = result[0][1]
	    #response = result[0][0]
	    #print response
            response = json.loads(result[0][0])
	    response["command-id"] = new_command_id
	    if command_count[0][0] > 1:
	    	response["eocq"] = "no"
	    else:
	    	response["eocq"] = "yes"
        else:
            response = []
	cursor.close()
        return response
	
    def deactivateCommand(self, command_id):
        """
        Deactivate command 
        """
	try:
		query = """ UPDATE meru_command SET command_status = 2 WHERE \
				command_id = '%s'""" % command_id
		cursor = connections['meru_cnms_sitegroup'].cursor()
		cursor.execute(query)
		cursor.close()
	except Exception as error:
		print error	

class DeviceApplication(View):

    """
    Restful implementation for Controller
    """
    false_response = {"status": False, "mac": ""}
    true_response = {"status": True, "mac": ""}

    @csrf_exempt
    def dispatch(self, *args, **kwargs):
        # dont worry about the CSRF here
        return super(DeviceApplication, self).dispatch(*args, **kwargs)

    def get(self, request):
        """
        To check whether specified mac has registered with the mac or not,
        performing is_registered
        :param request:
        :param args:
        :param kwargs:
        :return:
        """
        mac = request.GET.get('mac')

        if 'snum' in request.GET.keys():
            mac = request.GET.get('snum')

        self.true_response["status"] = "true"
        self.true_response["mac"] = mac
        self.false_response["status"] = "false"
        self.false_response["mac"] = mac

        query = "SELECT COUNT(1) FROM meru_device WHERE \
        `device_mac` = '%s'" % mac
	print "mysql access in get"
	print datetime.datetime.now()
        cursor = connections['meru_cnms_sitegroup'].cursor()
        cursor.execute(query)
	print "process complete"
	print datetime.datetime.now()
        result = cursor.fetchall()
        if not result[0][0]:
            return HttpResponse(json.dumps(self.false_response))
        return HttpResponse(json.dumps(self.true_response))

    def post(self, request):
        """

        Request:  Monitoring data from controller and insert that data into
        a mongoDB data source.
        Response: Respond with commands for the controller that has been
        registered by a user for that particular controller

        :param request:
        :param args:
        :param kwargs:
        :return:
        """
	memory_report = self.memory_usage()
        print "Memory Report"
        print memory_report
	mac = ""
	try:    
        	post_data = json.loads(request.body)
	except ValueError as e:
		print "Malformed json data from cntlr"
		print e
		return HttpResponse(json.dumps({"status" : "false", "mac-address" : \
		"No JSON object decoded"}))

        if 'snum' in post_data and re.match('([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})', post_data.get('snum')):
            mac = post_data.get('snum')
        elif 'mac' in post_data.get('msgBody').get('controller'):
            mac = post_data.get('msgBody').get('controller').get('mac')
	print str(mac)

	if isinstance(mac, str) and len(mac) is 0 or re.match('([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})', mac) is None:
		return HttpResponse(json.dumps({ "status" : "false", "mac-address" : \
			"No mac data from controller"}))
        no_mac = {"status": "false", "mac-address": mac}

	print "mysql access in post"
	print datetime.datetime.now()
        query = "SELECT COUNT(1) FROM meru_device WHERE \
        `device_mac` = '%s'" % mac
        cursor = connections['meru_cnms_sitegroup'].cursor()
        cursor.execute(query)
	print "process complete"
	print datetime.datetime.now()
        result = cursor.fetchall()
        if not result[0][0]:
            return HttpResponse(json.dumps(no_mac))

        utc_1970 = datetime.datetime(1970, 1, 1)
        utcnow = datetime.datetime.utcnow()
        timestamp = int((utcnow - utc_1970).total_seconds())

        post_data['timestamp'] = timestamp
        post_data['lower_snum'] = mac.lower()
        if 'controller' in post_data.get('msgBody'):
            self.type_casting(post_data)
        elif 'msolo' in post_data.get('msgBody'):
            self.msolo_type_casting(post_data)
        
        try:
            '''saving the complete data to db.devices until 
            the whole code is updated with splitting with new db'''
            #DB.devices.insert(post_data)
            if 'controller' in post_data.get('msgBody'):
                # spliiting data to save in device_alamrs
                post_data = self.process_alarms(post_data)
                #splitting data to save in device_clients
                post_data = self.process_clients(post_data)
                #splitting data to save in device_aps
                post_data = self.process_aps(post_data)
                process_con = self.process_controller(post_data)
            elif 'msolo' in post_data.get('msgBody'):
                # splitting msolo data to save in device_controllers collection
                process_msolo = self.process_msolo(post_data)
                # splitting msolo radio params data to save in device_radio_params collection
                process_msolo_radio_params = self.process_msolo_radio_params(post_data)
                # splitting msolo alarm data to save in device_alarms collection
                process_msolo_alarms = self.process_msolo_alarms(post_data)
                # splitting msolo clients data to save in device_clients collection
                process_msolo_clients = self.process_msolo_clients(post_data)
                # splitting msolo rouge aps data to save in device_rouge_ap collection
                process_msolo_rouge_ap = self.process_msolo_rouge_ap(post_data)
            print "db access in post:"
            print datetime.datetime.now()
            #DB.devices.insert(post_data)
            print "process complete at:"
            print datetime.datetime.now()
            
            
            
        except Exception, e:
            print "mongoDB error in post views.py"
            print e
        try:
            command_id = int(post_data.get('current-command-id')) if post_data.get('current-command-id') else 0
            if command_id is 0:
                # php api call
                host_ip = request.get_host().split(':')[0]
                device_type='controller'
                if 'msolo' in post_data.get('msgBody'):
                    device_type='msolo'
    	    	url = "http://" + str(host_ip) + settings.BASE_PATH +"command/device/create"
            	data = json.dumps({"mac" : mac,"device_type":str(device_type)})
            	headers = {'Content-Type': 'application/json'}
            	r = requests.post(url, data=data, headers=headers)
            	return HttpResponse(r.text)
            else:
                raw_model = Raw_Model()  # Raw model class to access the sql
                config_data = raw_model.isConfigData(mac, command_id)
		command_status = int(post_data.get('command-status'))
		#check command-status. If equals -1 then change status of current-command-id to 2 i.e inactive
		if command_status is -1:
			raw_model.deactivateCommand(command_id)


        except ValueError as error:
            print error
            return HttpResponse(json.dumps({"status" : "false", "mac" : "No JSON object decoded"}))

        return HttpResponse(json.dumps(config_data))


    def put(self, request, *args, **kwargs):
        """
        Update from the controller with info that all the commands has
        been successfully executed on that controller
        :param mac:
        :param request:
        :param args:
        :param kwargs:
        """
        self.true_response["mac"] = None
        self.false_response["mac"] = None
        put_data = json.loads(request.body)
        mac = ""

        if request.method == 'PUT':
            if "mac" in kwargs:
                mac = kwargs["mac"]
                self.true_response["mac"] = mac
                self.false_response["mac"] = mac
                query = "SELECT COUNT(1) FROM meru_device WHERE \
                `device_mac` = '%s'" % mac
                cursor = connections['meru_cnms_sitegroup'].cursor()
                cursor.execute(query)
                result = cursor.fetchall()
                if not result[0][0]:
                    return HttpResponse(json.dumps(self.false_response))
                if put_data["status"].lower() == "true":
                    try:
                        db = mydb.connect(host='localhost', user='root', db='meru_cnms_sitegroup', passwd='root')
                        query = """ UPDATE meru_command SET command_status = 2 WHERE \
                                command_mac = '%s'""" % mac
                        cursor = db.cursor()
                        cursor.execute(query)
                        db.commit()
                        cursor.close()
                        return HttpResponse(json.dumps(self.true_response))
                    except Exception as error:
                        print error
                        self.false_response["mac"] = mac
                        return HttpResponse(json.dumps(self.false_response))
                else:
                    return HttpResponse(json.dumps(self.false_response))
            else:
                        return HttpResponse(json.dumps({"status" : "false", "mac" : mac}))
        else:
                return HttpResponse("Method is Not Supported")

    ######################################
    """Controller data Processing in collections - device_controllers, device_aps,\
     device_alarms, device_clients"""
    ######################################
    def type_casting(self, doc):
        '''type casting the data received from controller , \
        converting required values to int'''
        
        if 'alarms' in doc.get('msgBody').get('controller'):
            for alarm in doc.get('msgBody').get('controller').get('alarms'):
                alarm['timeStamp'] = int(alarm['timeStamp'])

        if 'aps' in doc.get('msgBody').get('controller'):
            for ap_elem in doc.get('msgBody').get('controller').get('aps'):
                ap_elem['id'], ap_elem['rxBytes'] = int(ap_elem['id']), \
                 int(ap_elem['rxBytes'])
                ap_elem['txBytes'], ap_elem['wifiExp'] = \
                int(ap_elem['txBytes']),int(ap_elem['wifiExp'])

        if 'clients' in doc.get('msgBody').get('controller'):
            for client in doc.get('msgBody').get('controller').get('clients'):
                if str(client['apId']).isdigit():
                    client['apId'] = int(client['apId'])
                if str(client['wifiExp']).isdigit():
	               client['wifiExp'] = int(client['wifiExp'])
                client['rxBytes'] = int(client['rxBytes']) \
                if str(client['rxBytes']).isdigit() else 0
                client['txBytes'] = int(client['txBytes']) \
                if str(client['txBytes']).isdigit() else 0
                client['txBytes'] = int(client['txBytes']) \
                if str(client['txBytes']).isdigit() else 0

        return doc

    def process_alarms(self, doc):
        # splitting devices collection to new clients collection
        new_alarms_list = []
        alarm_row = []
        mac = doc.get('snum')
        timestamp = doc.get('timestamp') or 0
        if mac is None or re.match('([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})', mac) is None:
            mac = doc.get('msgBody').get('controller').get('mac')
	lower_snum = mac.lower()
        if 'alarms' in doc.get('msgBody').get('controller'):
            new_alarms_list = doc.get('msgBody').get('controller').get('alarms')
        try:
            cursor = DB.device_alarms.find({ "controller_mac" : mac}, { "alarms" : { "$slice" : -1}})
        except Exception as error:
            print "mongoDB error in process_alarms"
            print error
        for c in cursor:
            alarm_row.append(c)
        if len(alarm_row):
            last_alarm = alarm_row[0].get('alarms')[0]
            for alarm in new_alarms_list:
                if alarm["timeStamp"] > last_alarm["timeStamp"]:
                    DB.device_alarms.update({ "controller_mac" : mac}, { "$push" : \
			{ "alarms" : alarm}, "$set" : { "timestamp" : timestamp}})
        else:
    	    if len(new_alarms_list):
                	DB.device_alarms.insert({ "controller_mac" : mac, "timestamp":timestamp, \
			"lower_snum":lower_snum, "alarms" : new_alarms_list})
        try:
            doc.get('msgBody').get('controller')['alarms'] = []
        except KeyError as e:
            print "Exception at process_alarms"
            print e
        return doc

    def process_clients(self, doc):
        # splitting devices collection to new clients collection
        clients_list = []
	ap_info = {}
        mac = doc.get('snum')
	ap_list = doc.get('msgBody').get('controller').get('aps')
	for ap in ap_list:
		ap_info[ap.get('id')] = ap.get('mac')
        timestamp = doc.get('timestamp') or 0
        # get the clients data from controller data
        if mac is None or re.match('([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})', mac) is None:
            mac = doc.get('msgBody').get('controller').get('mac')
	lower_snum = mac.lower()
        if 'clients' in doc.get('msgBody').get('controller'):
            clients_list = doc.get('msgBody').get('controller').get('clients')
        
        for client in clients_list:
	    ap_id = client.get('apId')
	    if re.match('([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})', client.get('mac')) and ap_id in ap_info:
	    	ap_mac = ap_info.get(ap_id)
		try:
	    		DB.device_clients.insert({ "controller_mac" : mac, "ap_mac" : \
			ap_mac, "timestamp":timestamp, "lower_snum":lower_snum, \
			"clients" : client})
		except Exception as error:
			print "Mongodb error in process_clients"
			print error	
        try:
            doc.get('msgBody').get('controller')['clients'] = []
        except KeyError as e:
            print "Exception at process_clients"
            print e
        return doc

    def process_aps(self, doc):
        # splitting devices collection to new aps collection
        aps_list = []
        mac = doc.get('snum')
        timestamp = doc.get('timestamp') or 0
        # get the aps data from controller data
        if mac is None or re.match('([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})', mac) is None:
            mac = doc.get('msgBody').get('controller').get('mac')
        lower_snum = mac.lower()
        if 'aps' in doc.get('msgBody').get('controller'):
            aps_list = doc.get('msgBody').get('controller').get('aps')
        
        for ap in aps_list:
		if re.match('([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})', ap.get('mac')):
			try:
				DB.device_aps.insert({ "controller_mac" : mac, "timestamp":timestamp, \
				"lower_snum":lower_snum, "aps" : ap})
			except Exception as error:
				print "Mongodb error in process_aps"
				print error
        try:
            doc.get('msgBody').get('controller')['aps'] = []
        except KeyError as e:
            print "Exception at process_clients"
            print e
        return doc

    def process_controller(self, doc):
    	mac = doc.get('snum')
    	timestamp = doc.get('timestamp') or 0
    	if mac is None or re.match('([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})', mac) is None:
    		mac = doc.get('msgBody').get('controller').get('mac')
    	lower_snum = mac.lower()
    	opstatus = doc.get('msgBody').get('controller').get('operState')
    	util = doc.get('msgBody').get('controller').get('controllerUtil')
    	sec_state = doc.get('msgBody').get('controller').get('secState')
    	try:
    		DB.device_controllers.insert({ "lower_snum" : lower_snum, "timestamp" : timestamp, "operState" : opstatus,\
    					"utilization" : util, "secState" : sec_state})
    	except Exception as error:
    		print "Mongodb error in process_controller"
    		print error
    	return True

    ######################################
    """mSolo Processing in collections - device_msolo, device_radio_params,\
     device_alarms, device_clients"""
    ######################################
    def msolo_type_casting(self, doc):
        '''type casting the data received from msolo , \
        converting required values to int'''
        if 'msolo' in doc.get('msgBody'):
            rxBytes = int(doc.get('msgBody').get('msolo').get('rx-bytes') or 0)
            doc['msgBody']['msolo']['rx-bytes'] = rxBytes
            txBytes = int(doc.get('msgBody').get('msolo').get('tx-bytes') or 0) 
            doc['msgBody']['msolo']['tx-bytes'] = txBytes
            doc['msgBody']['msolo']['utilization'] = float(doc.get('msgBody').get('msolo').get('utilization'))\
            if float(doc['msgBody']['msolo']['utilization']) else 0
            
        if 'alarms' in doc.get('msgBody').get('msolo'):
            for alarm in doc.get('msgBody').get('msolo').get('alarms'):
                alarm['timeStamp'] = int(alarm['timeStamp'])

        if 'clients' in doc.get('msgBody').get('msolo'):
            for client in doc.get('msgBody').get('msolo').get('clients'):
                client['rxBytes'] = int(client['rxBytes']) \
                if str(client['rxBytes']).isdigit() else 0
                client['txBytes'] = int(client['txBytes']) \
                if str(client['txBytes']).isdigit() else 0
                client['rssi'] = int(client['rssi'])\
                if str(client['rssi']).isdigit() else 0
                client['rxPackets'] = int(client['rxPackets'])\
                if str(client['rxPackets']).isdigit() else 0
                client['txPackets'] = int(client['txPackets'])\
                if str(client['txPackets']).isdigit() else 0
                
        if 'radio-params' in doc.get('msgBody').get('msolo'):
            for radio in doc.get('msgBody').get('msolo').get('radio-params'):
                radio['rx-bytes'] = int(radio['rx-bytes']) \
                if str(radio['rx-bytes']).isdigit() else 0
                radio['tx-bytes'] = int(radio['tx-bytes']) \
                if str(radio['tx-bytes']).isdigit() else 0
                
        return doc

    def process_msolo_alarms(self, doc):
        # splitting msolo collection to clients collection
        new_alarms_list = []
        alarm_row = []
        mac = doc.get('snum')
        timestamp = doc.get('timestamp') or 0
        if mac is None or re.match('([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})', mac) is None:
            mac = doc.get('msgBody').get('msolo').get('mac')
        lower_snum = mac.lower()
        if 'alarms' in doc.get('msgBody').get('msolo'):
            new_alarms_list = doc.get('msgBody').get('msolo').get('alarms')
        try:
            cursor = DB.device_alarms.find({ "msolo_mac" : mac}, { "alarms" : { "$slice" : -1}})
        except Exception as error:
            print "mongoDB error in process_alarms"
            print error
        for c in cursor:
            alarm_row.append(c)
        if len(alarm_row):
            last_alarm = alarm_row[0].get('alarms')[0]
            for alarm in new_alarms_list:
                if alarm["timeStamp"] > last_alarm["timeStamp"]:
                    DB.device_alarms.update({ "msolo_mac" : mac}, { "$push" : \
            { "alarms" : alarm}, "$set" : { "timestamp" : timestamp}})
        else:
            if len(new_alarms_list):
                    DB.device_alarms.insert({ ",msolo_mac" : mac, "timestamp":timestamp, \
            "lower_snum":lower_snum, "alarms" : new_alarms_list})
        try:
            doc.get('msgBody').get('msolo')['alarms'] = []
        except KeyError as e:
            print "Exception at process_alarms"
            print e
        return doc

    def process_msolo_clients(self, doc):
        # splitting devices collection to new clients collection
        clients_list = []
        mac = doc.get('snum')
        timestamp = doc.get('timestamp') or 0
        # get the clients data from controller data
        if mac is None or re.match('([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})', mac) is None:
            mac = doc.get('msgBody').get('msolo').get('mac')
        lower_snum = mac.lower()
        if 'clients' in doc.get('msgBody').get('msolo'):
            clients_list = doc.get('msgBody').get('msolo').get('clients')
        
        for client in clients_list:
            try:
                DB.device_clients.insert({ "msolo_mac" : mac, \
                    "timestamp":timestamp, "lower_snum":lower_snum, \
                "clients" : client})
            except Exception as error:
                print "Mongodb error in process_clients"
                print error 
        try:
            doc.get('msgBody').get('msolo')['clients'] = []
        except KeyError as e:
            print "Exception at process_clients"
            print e
        return doc
    def process_msolo_rouge_ap(self, doc):
        # splitting devices collection to new clients collection
        rouge_ap_list = []
        mac = doc.get('snum')
        timestamp = doc.get('timestamp') or 0
        # get the clients data from controller data
        if mac is None or re.match('([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})', mac) is None:
            mac = doc.get('msgBody').get('msolo').get('mac')
        lower_snum = mac.lower()
        if 'rouge-aps' in doc.get('msgBody').get('msolo'):
            rouge_ap_list = doc.get('msgBody').get('msolo').get('rouge-aps')
        
        for ap in rouge_ap_list:
            try:
                DB.device_rouge_ap.insert({ "msolo_mac" : mac, \
                    "timestamp":timestamp, "lower_snum":lower_snum, \
                "rouge_ap" : ap})
            except Exception as error:
                print "Mongodb error in process_rouge_ap"
                print error 
        try:
            doc.get('msgBody').get('msolo')['rouge-aps'] = []
        except KeyError as e:
            print "Exception at process_rouge_ap"
            print e
        return doc

    def process_msolo(self, doc):
        mac = doc.get('snum')
        timestamp = doc.get('timestamp') or 0
        if mac is None or re.match('([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})', mac) is None:
            mac = doc.get('msgBody').get('msolo').get('mac')
        lower_snum = mac.lower()
        opstatus = doc.get('msgBody').get('msolo').get('operState')
        swVersion = doc.get('msgBody').get('msolo').get('swVersion')
        rxBytes = doc.get('msgBody').get('msolo').get('rx-bytes')
        txBytes = doc.get('msgBody').get('msolo').get('tx-bytes')
        generic_command_status = doc.get('msgBody').get('msolo').get('generic-command-status')
        generic_command_output = doc.get('msgBody').get('msolo').get('generic-command-output')
        utilization = doc.get('msgBody').get('msolo').get('utilization')
        try:
            DB.device_controllers.insert({ "lower_snum" : lower_snum, "timestamp" : timestamp,\
            "operState" : opstatus,"swVersion" : swVersion,"rxBytes":rxBytes, "txBytes":txBytes,\
            "generic_command_status":generic_command_status,"generic_command_output":generic_command_output,\
            "utilization":utilization})

        except Exception as error:
            print "Mongodb error in process_controller"
            print error
        return True

    def process_msolo_radio_params(self, doc):
        # splitting devices collection to new clients collection
        radio_params_list = []
        mac = doc.get('snum')
        timestamp = doc.get('timestamp') or 0
        # get the clients data from controller data
        if mac is None or re.match('([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})', mac) is None:
            mac = doc.get('msgBody').get('msolo').get('mac')
        lower_snum = mac.lower()
        if 'radio-params' in doc.get('msgBody').get('msolo'):
            radio_params_list = doc.get('msgBody').get('msolo').get('radio-params')
        
        for radio_param in radio_params_list:
        
        
            try:
                DB.device_radio_params.insert({ "msolo_mac" : mac, \
                    "timestamp":timestamp, "radio_params":radio_param})
            except Exception as error:
                print "Mongodb error in process_radio_params"
                print error 
        try:
            doc.get('msgBody').get('msolo')['radio-params'] = []
        except KeyError as e:
            print "Exception at process_clients"
            print e
        return doc
    
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


