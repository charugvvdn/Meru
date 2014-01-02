from django.http import HttpResponse, HttpResponseServerError
from django.db import connections, transaction
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q
from pymongo import MongoClient
from django.shortcuts import render, render_to_response
from django.template import RequestContext
import datetime
import itertools
from collections import Counter
import ast
import json

from test_1_app.models import controller, command, alarm, dashboard_info, \
    ssid, security_profile, ssid_in_command

from django.views.generic.base import View


# Connection with mongodb client
client = MongoClient()
db = client['nms']


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
                                  {"d": "AP with number of Clients Connected"}, context)

    return HttpResponseServerError()


class Reports():

    """
    Reports common functionality and features
    """
    pass


class Common():

    """
    Common functinality for all the modules
    """

    def traverse(self, obj, l):
        if hasattr(obj, '__iter__'):
            for o in obj:
                if isinstance(o, dict):
                    l.append(o)
                else:
                    self.traverse(o, l)
        return l

    def eval_request(self, request):
        if request.method == "GET":
            post_data = request.GET.dict()
            get_data = {}
            for pd in post_data:
                temp_var = ast.literal_eval(pd)
                for t in temp_var:
                    get_data[t] = temp_var[t]
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

        if 'time' in post_data:
            time_frame = post_data['time']
            start_time = time_frame[0]
            end_time = time_frame[1]

        else:
            utc_1970 = datetime.datetime(1970, 1, 1)
            utc_now = datetime.datetime.utcnow()
            offset = utc_now - datetime.timedelta(minutes=30)
            start_time = int((offset - utc_1970).total_seconds())
            end_time = int((utc_now - utc_1970).total_seconds())

        for mac in mac_list:
            if not db.devices.find({"snum": mac}).count():
                continue
            cursor = db.devices.find(
                {"snum": mac, "timestamp": {"$gt": start_time, "$lt": end_time}})

            for doc in cursor:
                doc_list.append(doc)

        return doc_list

    def calc_type(self, doc_list, get_type):
        """
        get the client list or the ap list or the alarm list on the basis of
        get_type. by default it is None
        """
        return_dict = {}
        for doc in doc_list:
            if get_type in doc['msgBody'].get('controller'):
                result = doc.get('msgBody').get('controller').get(get_type)
                for c in result:
                    unix_timestamp = int(doc['timestamp']) * 1000
                    if unix_timestamp not in return_dict:
                        return_dict[unix_timestamp] = []
                    return_dict[unix_timestamp].append(c)

        return return_dict

    def throughput_calc(self, clients):
        rx_list = []
        tx_list = []
        throughput = []

        for c in clients:
            rx = 0
            tx = 0
            for ts in clients[c]:
                rx += ts['rxBytes']
                tx += ts['txBytes']

            rx_list.append([c, rx])
            tx_list.append([c, tx])
            throughput.append([c, rx + tx])

        return (rx_list, tx_list, throughput)


class Raw_Model():

    """
    Raw SQL queries methods
    """

    def isConfigData(self, mac):
        """
        Generating the commands for the controller with
        given controller mac address passed as `mac`
        :param mac:
        """
        config_data = {}
        sec_profile_dict = {"sec-enc-mode": "", "sec-passphrase": "",
                            "sec-profile-name": "", "sec-l2-mode": ""}
        ess_profile_dict = {"ess-profile-name": "", "ess-dataplane-mode": "",
                            "ess-state": "", "ess-ssid-broadcast": "",
                            "ess-security-profile": ""}

        cursor = connections['nms_clone'].cursor()

        '''q = "SELECT ssid.ssid,\
        security_profile.security_profile_id ,\
        security_profile.enc_mode as\
            'sec-enc-mode',security_profile.passphrase as\
             'sec-passphrase',security_profile.profile_name as\
            'sec-profile-name',security_profile.l2_mode as\
             'sec-l2-mode',`ssid`.name as 'ess-profile-name',\
            `ssid`.dataplane_mode as \
            'ess-dataplane-mode',`ssid`.enabled as 'ess-state',\
            `ssid`.visible as 'ess-ssid-broadcast',\
            `security_profile`.profile_name as\
            'ess-security-profile' FROM  `ssid`\
                    LEFT JOIN\
             `security_profile` ON \
             (security_profile.security_profile_id=\
                `ssid`.security_profile_id)\
             INNER JOIN ssid_in_command ON \
             (ssid_in_command.ssid=`ssid`.ssid)\
             INNER JOIN command ON\
              (ssid_in_command.command_id=\
                `command`.command_id)\
              WHERE `command`.`controller_mac_address` = \
              '%s'  and (`command`.flag='0' or \
                `command`.flag='1')\
             ORDER BY  `command`.`timestamp` \
              ASC limit 0,1" % str(mac)'''

        q = """SELECT command_json FROM meru_command WHERE `command_mac` = '%s' \
                ORDER BY command_createdon DESC LIMIT 1""" % mac

        cursor.execute(q)
        result = cursor.fetchall()

        '''if len(result) != 0:
            if str(result[0][4]) == 'None':
                ess_profile_dict["ess-profile-name"] = str(result[0][6])
                ess_profile_dict["ess-dataplane-mode"] = str(result[0][7])
                ess_profile_dict["ess-state"] = str(result[0][8])
                ess_profile_dict["ess-ssid-broadcast"] = str(result[0][9])
                ess_profile_dict["ess-security-profile"] = str(result[0][10])

                config_data["ESSProfiles"] = [ess_profile_dict]
                config_data["status"] = "true"
                config_data["mac"] = str(mac)

            else:
                sec_profile_dict["sec-enc-mode"] = str(result[0][2])
                sec_profile_dict["sec-passphrase"] = str(result[0][3])
                sec_profile_dict["sec-profile-name"] = str(result[0][4])
                sec_profile_dict["sec-l2-mode"] = str(result[0][5])
                ess_profile_dict["ess-profile-name"] = str(result[0][6])
                ess_profile_dict["ess-dataplane-mode"] = str(result[0][7])
                ess_profile_dict["ess-state"] = str(result[0][8])
                ess_profile_dict["ess-ssid-broadcast"] = str(result[0][9])
                ess_profile_dict["ess-security-profile"] = str(result[0][10])

                config_data["SecurityProfiles"] = [sec_profile_dict]
                config_data["ESSProfiles"] = [ess_profile_dict]
                config_data["status"] = "true"
                config_data["mac"] = str(mac)
        else:
            return []'''
        if result:
            response = ast.literal_eval(result[0][0])
        else:
            response = []
        return response


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

    def get(self, request, *args, **kwargs):
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

        '''if controller.objects.filter(mac_address=mac).exists():
            self.true_response["mac"] = mac
            return HttpResponse(json.dumps(self.true_response))'''

        q = "SELECT COUNT(1) FROM meru_controller WHERE `controller_mac` = '%s'" % mac
        cursor = connections['nms_clone'].cursor()
        cursor.execute(q)
        result = cursor.fetchall()
        if not result[0][0]:
            self.false_response["status"] = "false"
            self.false_response["mac"] = mac
            return HttpResponse(json.dumps(self.false_response))
        self.true_response["status"] = "true"
        self.true_response["mac"] = mac
        return HttpResponse(json.dumps(self.true_response))

    def post(self, request, *args, **kwargs):
        """

        Request:  Monitoring data from controller and insert that data into
        a mongodb data source.
        Response: Respond with commands for the controller that has been
        registered by a user for that particular controller

        :param request:
        :param args:
        :param kwargs:
        :return:
        """
        post_data = json.loads(request.body)

        if 'snum' in post_data.keys():
            mac = post_data.get('snum')
        else:
            mac = post_data.get('controller')

        no_mac = {"status": "false", "mac": mac}

        '''if not controller.objects.filter(mac_address=mac).exists():
            return HttpResponse(json.dumps(no_mac))'''

        q = "SELECT COUNT(1) FROM meru_controller WHERE `controller_mac` = '%s'" % mac
        cursor = connections['nms_clone'].cursor()
        cursor.execute(q)
        result = cursor.fetchall()
        if not result[0][0]:
            return HttpResponse(json.dumps(no_mac))

        utc_1970 = datetime.datetime(1970, 1, 1)
        utcnow = datetime.datetime.utcnow()
        timestamp = int((utcnow - utc_1970).total_seconds())

        post_data['timestamp'] = timestamp
        self.type_casting(post_data)
        print post_data
        db.devices.insert(post_data)

        raw_model = Raw_Model()  # Raw model class to access the sql
        config_data = raw_model.isConfigData(mac)

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
        if "mac" in kwargs:
            mac = kwargs["mac"]
        else:
            return HttpResponse(json.dumps(self.false_response))
        null_mac = {"status": "Null mac"}
        not_registered = {"status": "not registered"}

        self.true_response["mac"] = mac
        self.false_response["mac"] = mac
        self.false_response["status"] = "false"

        q = "SELECT COUNT(1) FROM meru_controller WHERE `controller_mac` = '%s'" % mac
        cursor = connections['nms_clone'].cursor()
        cursor.execute(q)
        result = cursor.fetchall()
        if not result[0][0]:
            return HttpResponse(json.dumps(self.false_response))

        try:
            q = """ UPDATE meru_command SET command_status = 2 WHERE \
                    command_mac = '%s'""" % mac
            cursor = connections['nms_clone'].cursor()
            cursor.execute(q)
            return HttpResponse(json.dumps(self.true_response))

        except Exception as e:
            print str(e)
            return HttpResponse(json.dumps(self.false_response))

    def type_casting(self, doc):
        alarms = []
        aps = []
        clients = []
        alarms = doc.get('msgBody').get('controller').get('alarms')
        aps = doc.get('msgBody').get('controller').get('aps')
        clients = doc.get('msgBody').get('controller').get('clients')

        if 'alarms' in doc.get('msgBody').get('controller'):
            for alarm in doc.get('msgBody').get('controller').get('alarms'):
                alarm['timeStamp'] = int(alarm['timeStamp'])

        if 'aps' in doc.get('msgBody').get('controller'):
            for ap in doc.get('msgBody').get('controller').get('aps'):
                ap['id'], ap['rxBytes'] = int(ap['id']), int(ap['rxBytes'])
                ap['txBytes'], ap['wifiExp'] = int(ap['txBytes']), int(ap['wifiExp'])

        if 'clients' in doc.get('msgBody').get('controller'):
            for client in doc.get('msgBody').get('controller').get('clients'):
                client['apId'], client['rxBytes'] = int(client['apId']), int(client['rxBytes'])
                client['txBytes'], client['txBytes'] = int(client['txBytes']), int(client['txBytes'])

        return doc


def client_throughput(request):
    '''Module to plot the Station throughput line chart containing rxByte,
    txByte and throughput plotting of Clients'''
    clients = []
    throughput = []
    rx_list = []
    tx_list = []
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

        # start the report evaluation
        # get the clients
        get_type = "clients"
        clients = common.calc_type(doc_list, get_type)

        rx_list, tx_list, throughput = common.throughput_calc(clients)

        response_list = [
            {"label": "rxBytes", "data": rx_list},
            {"label": "txBytes", "data": tx_list},
            {"label": "throughput", "data": throughput}
        ]

        response = HttpResponse(json.dumps({"status": "true",
                                            "values": response_list,
                                            "message": "values for client throughput bar graph"}))

        return response

    else:
        return HttpResponse(json.dumps({"status": "false",
                                        "message": "No mac provided"}))


def devicetype(request):
    '''Module to plot the device type distribution pie chart'''

    device_types = {}
    response = []
    context = RequestContext(request)

    common = Common()
    post_data = common.eval_request(request)

    if 'mac' in post_data:
        # fetch the docs
        doc_list = common.let_the_docs_out(post_data)
        for doc in doc_list:
        # start the report evaluation

        # get the clients
            get_type = "clients"
            client_list = common.calc_type(doc_list, get_type)
            clients = doc.get('msgBody').get('controller').get('clients')

            for c in clients:
                if c['clientType'] in device_types:
                    device_types[c['clientType']] += 1
                else:
                    device_types[c['clientType']] = 1
        for d, n in device_types.iteritems():
            d1 = {"label": 0, "data": 0}
            d1["label"] = d
            d1["data"] = n
            response.append(d1)

        response = HttpResponse(json.dumps({"status": "true",
                                            "values": response}))
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
    unix_timestamp = 0

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

    rx_bytes = 0
    tx_bytes = 0
    throughput = []
    rx_list = []
    tx_list = []
    response_list = 0
    unix_timestamp = 0

    common = Common()
    post_data = common.eval_request(request)

    if not len(post_data):
        return HttpResponse(json.dumps({"status": "false",
                                        "message": "No POST data"}))

    if 'mac' in post_data:
        # fetch thdevicedistdevicedistdevicedistdevicedistdevicediste docs
        doc_list = common.let_the_docs_out(post_data)

        get_type = "aps"
        aps = common.calc_type(doc_list, get_type)

        get_type = "clients"
        clients = common.calc_type(doc_list, get_type)

        out_dict = aps

        # join both the dicts
        for times in out_dict:
            for client in clients[times]:
                out_dict[times].append(client)

        # get overall result
        rx_list, tx_list, throughput = common.throughput_calc(out_dict)

        response_list = [{"label": "rxBytes", "data": rx_list},
                         {"label": "txBytes", "data":
                          tx_list}, {"label": "throughput", "data": throughput}]
        response = HttpResponse(json.dumps({"status": "true",
                                            "values": response_list,
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

        for doc in doc_list:
            min_cl = min_ap = 100
            max_cl = max_ap = 0
            if 'aps' in doc['msgBody'].get('controller'):
                aps = doc.get('msgBody').get('controller').get('aps')
                for ap in aps:
                    if min_ap > ap["wifiExp"]:
                        min_ap = ap["wifiExp"]
                    if max_ap < ap["wifiExp"]:
                        max_ap = ap["wifiExp"]
                    unix_timestamp = int(doc['timestamp']) * 1000
                    ap['timestamp'] = unix_timestamp
                    clients.append(ap)
                    wifiexp_ap_sum += ap['wifiExp']
                    aps_count += 1
                avg_ap_wifiexp.append([unix_timestamp,
                                       wifiexp_ap_sum / aps_count])
                min_aplist.append([unix_timestamp, min_ap])
                max_aplist.append([unix_timestamp, max_ap])
            if 'clients' in doc['msgBody'].get('controller'):
                client = doc.get('msgBody').get('controller').get('clients')
                for c in client:
                    if min_cl > c["wifiExp"]:
                        min_cl = c["wifiExp"]
                    if max_cl < c["wifiExp"]:
                        max_cl = c["wifiExp"]

                    unix_timestamp = int(doc['timestamp']) * 1000
                    c['timestamp'] = unix_timestamp
                    clients.append(c)
                    wifiexp_cl_sum += c['wifiExp']
                    client_count += 1
                avg_cl_wifiexp.append([unix_timestamp,
                                       wifiexp_cl_sum / client_count])
                min_clist.append([unix_timestamp, min_cl])
                max_clist.append([unix_timestamp, max_cl])

        response_list = [
            {"label": "Maximum-Client-wifiExp", "data": max_clist},
            {"label": "Minimum-Client-wifiExp", "data": min_clist},
            {"label": "Maximum-AP-wifiExp", "data": max_aplist},
            {"label": "Minimum-AP-wifiExp", "data": min_aplist},
            {"label": "Average-AP-wifiExp", "data": avg_ap_wifiexp},
            {"label": "Average-client-wifiExp", "data": avg_cl_wifiexp}
        ]
        response = HttpResponse(json.dumps({"status": "true",
                                            "values": response_list,
                                            "message": "values for Wifi Experience bar graph"}))

        return response

    return HttpResponse(json.dumps({"status": "false",
                                    "message": "No mac provided"}))


def ap_clients(request):
    """ Plotting Graph for "Ap having clients connected to them "bar chart"""
    db = MongoClient()['nms']
    doc_list = []
    ap_dict = {}
    result = Counter()
    clients = []
    no_of_client = {}
    response_list = []
    list_new = []

    common = Common()
    post_data = common.eval_request(request)

    if not len(post_data):
        return HttpResponse(json.dumps({"status": "false",
                                        "message": "No POST data"}))

    if 'mac' in post_data:
        mac_list = post_data['mac']
        if 'time' in post_data:
            time_frame = post_data['time']
            start_time = time_frame[0]
            end_time = time_frame[1]

        else:
            utc_1970 = datetime.datetime(1970, 1, 1)
            utc_now = datetime.datetime.utcnow()
            offset = utc_now - datetime.timedelta(minutes=30)
            start_time = int((offset - utc_1970).total_seconds())
            end_time = int((utc_now - utc_1970).total_seconds())

        cursor = db.devices.find(
            {"snum": mac_list[0], "timestamp": {"$gt": start_time, "$lt": end_time}})

        for doc in cursor:
            doc_list.append(doc)

        for doc in doc_list:
            unix_timestamp = int(doc['timestamp']) * 1000
            min_cl = min_ap = 100
            max_cl = max_ap = 0
            if 'aps' in doc['msgBody'].get('controller'):
                aps = doc.get('msgBody').get('controller').get('aps')
                for ap in aps:

                    if ap['id'] not in ap_dict:
                        ap_dict[ap['id']] = ap['mac']
                        ap_dict[str(ap['id']) + "time"] = unix_timestamp

            if 'clients' in doc['msgBody'].get('controller'):
                client = doc.get('msgBody').get('controller').get('clients')
                for c in client:
                    client_dict = {}
                    client_dict['apId'] = c['apId']
                    clients.append(client_dict)

        for client in clients:

            response = {}
            if client['apId'] in ap_dict:
                result[str(client['apId'])] += 1

        for apid, count in result.iteritems():

            response = {}
            list_new = []
            list_new.append([ap_dict[str(apid) + "time"], result[str(apid)]])
            response['data'] = list_new
            response['label'] = ap_dict[int(apid)]
            response_list.append(response)

        response = HttpResponse(json.dumps({"status": "true",
                                            "values": response_list,
                                            "message": "values for Number of clients for AP"}))

        return response

    return HttpResponse(json.dumps({"status": "false",
                                    "message": "No mac provided"}))
