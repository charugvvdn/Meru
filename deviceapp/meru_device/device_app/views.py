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
from device_app.models import controller, command, alarm, dashboard_info, \
    ssid, security_profile, ssid_in_command
from django.views.generic.base import View
TIME_INDEX = 60

# Connection with mongoDB client
try:
    CLIENT = MongoClient()
    DB = CLIENT['nms']
except pymongo.errors.PyMongoError, e:
    print "Views.py -->"
    print e


def welcome(request):
    """

    Module for accessing the reports Api and display the graph plots
    """
    context = RequestContext(request)
    if 'station' in request.GET:
        return render_to_response('test_1_app/stationthru.html',
                                  {"d": "Station"}, context)
    if 'ap' in request.GET:
        return render_to_response('test_1_app/apthru.html',
                                  {"d": "AP"}, context)
    if 'wifi' in request.GET:
        return render_to_response('test_1_app/wifiexp.html',
                                  {"d": "Wifi Experience"}, context)
    if 'overall' in request.GET:
        return render_to_response('test_1_app/overallthru.html',
                                  {"d": "Overall Throughput"}, context)
    if 'dist' in request.GET:
        return render_to_response('test_1_app/devicedist.html',
                                  {"d": "Device Dist Throughput"}, context)
    if 'ap_client' in request.GET:
        return render_to_response('test_1_app/Ap-clients.html',
                                  {"d": "AP with number of Clients Connected"},\
                                   context)

    return HttpResponseServerError()


class Reports():

    """
    Reports common functionality and features
    """
    pass


class Common():
    """Common functinality for all the modules"""
    
    def traverse(self, obj, item):
        ''' common functinality'''
        if hasattr(obj, '__iter__'):
            for elem in obj:
                if isinstance(elem, dict):
                    item.append(elem)
                else:
                    self.traverse(elem, item)
        return item

    def eval_request(self, request):
        ''' Evaluate the requested query parameter and returns the post data'''
        if request.method == "GET":
            post_data = request.GET.dict()
            get_data = {}
            for data in post_data:
                temp_var = ast.literal_eval(data)
                for val in temp_var:
                    get_data[val] = temp_var[val]
            post_data = get_data

        elif request.method == "POST":
            post_data = json.loads(request.body)

        else:
            post_data = None

        return post_data

    def let_the_docs_out(self, post_data):
        """
        find all the docs on the basis of list of MACS and time frame
        """
        doc_list = []
        mac_list = post_data['mac']

        if 'time' in post_data and post_data['time']:
            time_frame = post_data['time']
            start_time = time_frame[0]
            end_time = time_frame[1]

        else:
            utc_1970 = datetime.datetime(1970, 1, 1)
            utc_now = datetime.datetime.utcnow()
            offset = utc_now - datetime.timedelta(minutes=30)
            start_time = int((offset - utc_1970).total_seconds())
            end_time = int((utc_now - utc_1970).total_seconds())

        try:
            for mac in mac_list:
                print "db access in let_the_docs_out:"
                print datetime.datetime.now()
                if not DB.devices.find({"lower_snum": mac.lower()}).count():
                    continue
                cursor = DB.devices.find({"lower_snum": mac.lower(), "timestamp" \
                    : {"$gt": start_time, "$lt": end_time}})
                

                for doc in cursor:
                    doc_list.append(doc)

            return doc_list
        except Exception, e:
            print e
            return doc_list

    def calc_type(self, doc_list, get_type):
        """
        get the client list or the ap list or the alarm list on the basis of
        get_type. by default it is None
        """
        return_dict = {}
        
        for doc in doc_list:
            if 'msgBody' in doc and 'controller' in doc['msgBody']:
                if get_type in doc['msgBody'].get('controller'):
                    result = doc.get('msgBody').get('controller').get(get_type)
                    for val in result:
                        unix_timestamp = int(doc['timestamp']) * 1000
                        if unix_timestamp not in return_dict:
                            return_dict[unix_timestamp] = []
                        return_dict[unix_timestamp].append(val)

        return return_dict

    def throughput_calc(self, clients):
        '''Function for client, ap, overall throughput, 
        rx, tx byte calculation'''
        rx_list = []
        tx_list = []
        throughput = []
        unix_time = 0
        rcv_bytes = 0
        currenttime = 0
        trnsfr_bytes = 0
        flag = 0
        #sorting the clients dict in ascending
        clients = OrderedDict(sorted(clients.items(), key=lambda t: t[0])) 
        for client in clients:
            # read the first timestamp of the clients dict
            currenttime = int(client/1000)
            break
        
        torange = currenttime + TIME_INDEX # a time range group
        
        for client in clients:
            if int(client / 1000) not in range(currenttime , torange ):
                ''' if the result exceed the time frame , append 
                the previous group of results and start to make a new group'''
                rx_list.append([unix_time, rcv_bytes])
                tx_list.append([unix_time, trnsfr_bytes])
                throughput.append([unix_time, rcv_bytes + trnsfr_bytes])
                currenttime = int(client/1000)
                torange = currenttime + TIME_INDEX
                rcv_bytes = 0
                trnsfr_bytes = 0
                flag = 0
                
            if int(client/1000) in range(currenttime , torange ):
                # grouping the result for above timeframe
                for elem in clients[client]:
                    rcv_bytes += int(elem['rxBytes'])
                    trnsfr_bytes += int(elem['txBytes'])
                unix_time = client
                flag = 1

        if flag == 1:
            # appending the last group of result
            rx_list.append([unix_time, rcv_bytes])
            tx_list.append([unix_time, trnsfr_bytes])
            throughput.append([unix_time, rcv_bytes + trnsfr_bytes])

        return (rx_list, tx_list, throughput)


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

        cursor = connections['meru_cnms_dev'].cursor()


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
		cursor = connections['meru_cnms_dev'].cursor()
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

        query = "SELECT COUNT(1) FROM meru_controller WHERE \
        `controller_mac` = '%s'" % mac
	print "mysql access in get"
	print datetime.datetime.now()
        cursor = connections['meru_cnms_dev'].cursor()
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
        query = "SELECT COUNT(1) FROM meru_controller WHERE \
        `controller_mac` = '%s'" % mac
        cursor = connections['meru_cnms_dev'].cursor()
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
        self.type_casting(post_data)
        
        try:
            '''saving the complete data to db.devices until 
            the whole code is updated with splitting with new db'''
            DB.devices.insert(post_data)

            # spliiting data to save in device_alamrs
            post_data = self.process_alarms(post_data)
            #splitting data to save in device_clients
            post_data = self.process_clients(post_data)
            #splitting data to save in device_aps
            post_data = self.process_aps(post_data)
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
	    	url = "http://54.186.33.61/command/controller/create"
        	data = json.dumps({"mac" : mac})
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
                query = "SELECT COUNT(1) FROM meru_controller WHERE \
                `controller_mac` = '%s'" % mac
                cursor = connections['meru_cnms_dev'].cursor()
                cursor.execute(query)
                result = cursor.fetchall()
                if not result[0][0]:
                    return HttpResponse(json.dumps(self.false_response))
                if put_data["status"].lower() == "true":
                    try:
                        db = mydb.connect(host='localhost', user='root', db='meru_cnms_dev', passwd='root')
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
        lower_snum = mac.lower()
        timestamp = doc.get('timestamp') or 0
        if mac is None:
            mac = doc.get('msgBody').get('controller').get('mac')
        if 'alarms' in doc.get('msgBody').get('controller'):
            new_alarms_list = doc.get('msgBody').get('controller').get('alarms')
        
        try:
            cursor = DB.device_alarms.find({ "mac" : mac}, { "alarms" : { "$slice" : -1}})
        except Exception as error:
            print "mongoDB error in process_alarms"
            print error
        for c in cursor:
            alarm_row.append(c)
        if len(alarm_row):
            last_alarm = alarm_row[0].get('alarms')[0]
            for alarm in new_alarms_list:
                if alarm["timeStamp"] > last_alarm["timeStamp"]:
                    DB.device_alarms.update({ "mac" : mac}, { "$push" : { "alarms" : alarm}})
        else:
    	    if len(new_alarms_list):
                	DB.device_alarms.insert({ "controller_mac" : mac, "timestamp":timestamp, \
			"lower_snum":lower_snum, "alarms" : new_alarms_list})
        try:
            pass
            doc.get('msgBody').get('controller')['alarms'] = []
        except KeyError as e:
            print "Exception at process_alarms"
            print e
        return doc

    def process_clients(self, doc):
        # splitting devices collection to new clients collection
        clients_list = []
        mac = doc.get('snum')
        timestamp = doc.get('timestamp') or 0
        # get the clients data from controller data
        if mac is None or re.match('([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})', mac) is None:
            mac = doc.get('msgBody').get('controller').get('mac')
	lower_snum = mac.lower()
        if 'clients' in doc.get('msgBody').get('controller'):
            clients_list = doc.get('msgBody').get('controller').get('clients')
        
        for client in clients_list:
	    if re.match('([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})', client.get('mac')):
            	DB.device_clients.insert({ "controller_mac" : mac, "timestamp":timestamp, "lower_snum":lower_snum, "clients" : client})
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
			DB.device_aps.insert({ "controller_mac" : mac, "timestamp":timestamp, "lower_snum":lower_snum, "aps" : ap})
        try:
            doc.get('msgBody').get('controller')['aps'] = []
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


def client_throughput(request):
    '''Module to plot the Station throughput line chart containing rxByte,
    txByte and throughput plotting of Clients'''
    clients = []
    throughput = []
    rx_list = []
    tx_list = []
    response_list = 0
    common = Common()
    post_data = common.eval_request(request)

    if not len(post_data):
        return HttpResponse(json.dumps({"status": "false",
                                        "message": "No POST data"}))

    if 'mac' in post_data:
        # fetch the docs
        doc_list = common.let_the_docs_out(post_data)

        # start the report evaluation
        # get the clients
        get_type = "clients"
        clients = common.calc_type(doc_list, get_type)

        rx_list, tx_list, throughput = common.throughput_calc(clients)

        response_list = [
                            {"label": "rxBytes", "data": rx_list}, \
                            {"label": "txBytes", "data": tx_list}, \
                            {"label": "throughput", "data": throughput}
                        ]
        
        response = HttpResponse(json.dumps({"status": "true", \
            "values": response_list,\
            "message": "values for client throughput bar graph"}))

        return response

    else:
        pass
    return HttpResponse(json.dumps({"status": "false"}))


def ap_throughput(request):
    """
    Total throughput of the access points
    """

    clients = []
    throughput = []
    rx_list = []
    tx_list = []
    response_list = 0
    

    common = Common()
    post_data = common.eval_request(request)

    if not len(post_data):
        return HttpResponse(json.dumps({"status": "false",
                                        "message": "No POST data"}))

    if 'mac' in post_data:
        # fetch the docs
        doc_list = common.let_the_docs_out(post_data)
        # start the report evaluation
        # get the clients
        get_type = "aps"
        clients = common.calc_type(doc_list, get_type)

        rx_list, tx_list, throughput = common.throughput_calc(clients)

        response_list = [
            {"label": "rxBytes", "data": rx_list},
            {"label": "txBytes", "data": tx_list},
            {"label": "throughput", "data": throughput}
        ]
        response = HttpResponse(json.dumps(
            {
                                "status": "true",
                                "values": response_list,
                                "message": "values for AP throughput bar graph"
                            }))

        return response
    else:
        return HttpResponse(json.dumps({"status": "false",
                                        "message": "No mac provided"}))


def overall_throughput(request):
    ''' Module to plot the overall throughput graph (rxBytes for AP + rxbytes
        for Client, txbyte for Ap+ txByte for Client, and throughput
        (rxbyte+txbyte)'''
    throughput = []
    rx_list = []
    tx_list = []
    response_list = 0
    

    common = Common()
    post_data = common.eval_request(request)

    if not len(post_data):
        return HttpResponse(json.dumps({"status": "false",
                                        "message": "No POST data"}))

    if 'mac' in post_data:
        # fetch the docs
        doc_list = common.let_the_docs_out(post_data)

        get_type = "aps"
        aps = common.calc_type(doc_list, get_type)

        get_type = "clients"
        clients = common.calc_type(doc_list, get_type)

        out_dict = aps
        
        # join both the dicts
        for times in out_dict:
            if len(clients):
                for key,val in clients.iteritems():
                    if key == times:
                        out_dict[times].extend(clients[times])

        # get overall result
        #print "out_dict",out_dict
        rx_list, tx_list, throughput = common.throughput_calc(out_dict)

        response_list = [{"label": "rxBytes", "data": rx_list}, \
        {"label": "txBytes", "data": \
            tx_list}, {"label": "throughput", "data": throughput}]
        
        response = HttpResponse(json.dumps({"status": "true", \
            "values": response_list,\
             "message": "values for Overall throughput bar graph"}))
        return response

    return HttpResponse(json.dumps({"status": "false",
                                    "message": "No mac provided"}))


def wifi_experience(request):
    """ Plotting Graph for Average Wifi Experience
     for Ap and Client along with the minimum and maximum values
    :param request:
     """

    clients = []
    avg_ap_wifiexp = []
    avg_cl_wifiexp = []
    min_aplist = []
    max_aplist = []
    min_clist = []
    max_clist = []
    aps_count = 0
    aps = client = []
    ap_flag = 0
    cl_flag = 0
    aps_count = 0
    wifiexp_ap_sum = 0
    min_cl = min_ap = 100
    max_cl = max_ap = 0
    client_count = 0
    wifiexp_ap_sum = 0
    wifiexp_cl_sum = 0
    response_list = 0
    unix_timestamp = 0
    common = Common()
    post_data = common.eval_request(request)

    if not len(post_data):
        return HttpResponse(json.dumps({"status": "false",
                                        "message": "No POST data"}))

    if 'mac' in post_data:
        # fetch the docs
        doc_list = common.let_the_docs_out(post_data)
        # sorting the doc_list dictionary in asc
        doc_list =  sorted(doc_list, key=lambda x: x['timestamp'])
        if not len(doc_list):
            return HttpResponse(json.dumps(\
                {"status": "false","message": "No filtered data received"}\
                ))
        # currentime  = first timestamp of the dict
        
        currenttime = doc_list[0]['timestamp'] 
        # grouping the timeframe
        torange = currenttime+TIME_INDEX
        min_cl = min_ap = 100
        max_cl = max_ap = 0
        for doc in doc_list:
            if 'msgBody' in doc and 'controller' in doc['msgBody']:
                aps = doc.get('msgBody').get('controller').get('aps') or []
                if 'clients' in doc['msgBody'].get('controller'):
                    client = doc.get('msgBody').get('controller').\
                    get('clients')

                if int(doc['timestamp']) not in range(currenttime , torange ):
                    
                    avg_ap_wifiexp.append([unix_timestamp , \
                        wifiexp_ap_sum / aps_count if aps_count > 0 else 0])
                    min_aplist.append([unix_timestamp , min_ap])
                    max_aplist.append([unix_timestamp , max_ap])

                    avg_cl_wifiexp.append([unix_timestamp , \
                        wifiexp_cl_sum / client_count if client_count > 0 \
                        else 0])
                    min_clist.append([unix_timestamp , min_cl])
                    max_clist.append([unix_timestamp , max_cl])
                    currenttime = doc['timestamp']
                    torange = currenttime+TIME_INDEX
                    ap_flag = 0
                    cl_flag = 0
                    aps_count = 0
                    wifiexp_ap_sum = 0
                    min_cl = min_ap = 100
                    max_cl = max_ap = 0

            if int(doc['timestamp']) in range(currenttime , torange ):

                for ap_elem in aps:
                    if 'wifiExp' in ap_elem:
                        if min_ap > int(ap_elem["wifiExp"]):
                            min_ap = int(ap_elem["wifiExp"])
                        if max_ap < int(ap_elem["wifiExp"]):
                            max_ap = int(ap_elem["wifiExp"])
                        unix_timestamp = int(doc['timestamp']) * 1000
                        ap_elem['timestamp'] = unix_timestamp
                        clients.append(ap_elem)
                        wifiexp_ap_sum += int(ap_elem['wifiExp'])
                        aps_count += 1
                        ap_flag = 1

                for cl_elem in client:
                    if 'wifiExp' in cl_elem:
                        if min_cl > int(cl_elem["wifiExp"]):
                            min_cl = int(cl_elem["wifiExp"])
                        if max_cl < int(cl_elem["wifiExp"]):
                            max_cl = int(cl_elem["wifiExp"])

                        unix_timestamp = int(doc['timestamp']) * 1000
                        cl_elem['timestamp'] = unix_timestamp
                        clients.append(cl_elem)
                        wifiexp_cl_sum += int(cl_elem['wifiExp'])
                        client_count += 1
                        cl_flag = 1

        if ap_flag == 1:
            avg_ap_wifiexp.append([unix_timestamp , \
             wifiexp_ap_sum / aps_count if aps_count > 0 else 0])
            min_aplist.append([unix_timestamp , min_ap])
            max_aplist.append([unix_timestamp , max_ap])
        if cl_flag == 1:
            avg_cl_wifiexp.append([unix_timestamp , \
             wifiexp_cl_sum / client_count if client_count > 0 else 0])
            min_clist.append([unix_timestamp , min_cl])
            max_clist.append([unix_timestamp , max_cl])


        response_list = [
            {"label": "Maximum-Client-wifiExp", "data": max_clist},
            {"label": "Minimum-Client-wifiExp", "data": min_clist},
            {"label": "Maximum-AP-wifiExp", "data": max_aplist},
            {"label": "Minimum-AP-wifiExp", "data": min_aplist},
            {"label": "Average-AP-wifiExp", "data": avg_ap_wifiexp},
            {"label": "Average-client-wifiExp", "data": avg_cl_wifiexp}
        ]
        
        response = HttpResponse(json.dumps({"status": "true", \
         "values": response_list,\
         "message": "values for Wifi Experience bar graph"}))
        return response

    return HttpResponse(json.dumps({"status": "false",
                                    "message": "No mac provided"}))


def ap_clients(request):
    """ Plotting Graph for "Ap having clients connected to them "bar chart"""
    
    doc_list = []
    ap_dict = {}
    result = Counter()
    clients = []
    response_list = []
    list_new = []
    post_data = json.loads(request.body)

    common = Common()
    if not len(post_data):
        return HttpResponse(json.dumps({"status": "false",
                                        "message": "No POST data"}))

    if 'mac' in post_data:
        doc_list = common.let_the_docs_out(post_data)
        for doc in doc_list:
            unix_timestamp = int(doc['timestamp']) * 1000
            if 'msgBody' in doc and 'controller' in doc['msgBody']:
                if 'aps' in doc['msgBody'].get('controller'):
                    aps = doc.get('msgBody').get('controller').get('aps')
                    for ap_elem in aps:

                        if ap_elem['id'] not in ap_dict:
                            ap_dict[ap_elem['id']] = ap_elem['mac']
                            ap_dict[str(ap_elem['id']) + "time"] = \
                            unix_timestamp

                if 'clients' in doc['msgBody'].get('controller'):
                    client = doc.get('msgBody').get('controller')\
                    .get('clients')
                    for cl_elem in client:
                        client_dict = {}
                        client_dict['apId'] = int(cl_elem['apId'])
                        clients.append(client_dict)

        for client in clients:

            response = {}
            if client['apId'] in ap_dict:
                result[str(client['apId'])] += 1
        
        for apid , count in result.iteritems()  :
            
            response = {}
            list_new = []
            list_new.append( [ap_dict[str(apid)+"time"] , result[str(apid)]])
            response['data']  = list_new
            response['label'] = ap_dict[int(apid)]
            response_list.append(response)
        
        #result = {"label": mac, "data": [timestamp,no_mac]}
        #response_list.append(result)

        response =  HttpResponse(json.dumps({"status": "true", \
         "values": response_list,\
         "message": "values for Number of clients for AP"}))
        return response

    return HttpResponse(json.dumps({"status": "false",
                                    "message": "No mac provided"}))

def devicetype(request):
    '''Module to plot the device type distribution pie chart'''

    device_types = {}
    response = []
    clients = []
    common = Common()
    post_data = common.eval_request(request)

    if 'mac' in post_data:
        # fetch the docs
        doc_list = common.let_the_docs_out(post_data)
        for doc in doc_list:
        # start the report evaluation

        # get the clients
            get_type = "clients"
            
            if 'msgBody' in doc and 'controller' in doc['msgBody']:
                clients = doc.get('msgBody').get('controller').\
                get('clients') or []
            
            for cl_elem in clients:
                if cl_elem['clientType'] in device_types:
                    device_types[cl_elem['clientType']] += 1
                else:
                    device_types[cl_elem['clientType']] = 1
        for key, value in device_types.iteritems():
            device = {"label": 0, "data": 0}
            device["label"] = key
            device["data"] = value
            response.append(device)

        response = HttpResponse(json.dumps({"status": "true",
                                            "values": response}))
        return response

    else:
        pass
    return HttpResponse(json.dumps({"status": "false"}))
