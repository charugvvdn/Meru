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
from collections import Counter, OrderedDict
import ast
import json

from reports.models import controller, command, alarm, dashboard_info, \
    ssid, security_profile, ssid_in_command

from django.views.generic.base import View
TIME_INDEX = 60

# Connection with mongoDB client
CLIENT = MongoClient()
DB = CLIENT['nms']


def welcome(request):
    """

    Module for accessing the reports Api and display the graph plots
    """
    context = RequestContext(request)
    if 'station' in request.GET:
        return render_to_response('reports_template/stationthru.html',
                                  {"d": "Station"}, context)
    if 'ap' in request.GET:
        return render_to_response('reports_template/apthru.html',
                                  {"d": "AP"}, context)
    if 'wifi' in request.GET:
        return render_to_response('reports_template/wifiexp.html',
                                  {"d": "Wifi Experience"}, context)
    if 'overall' in request.GET:
        return render_to_response('reports_template/overallthru.html',
                                  {"d": "Overall Throughput"}, context)
    if 'dist' in request.GET:
        return render_to_response('reports_template/devicedist.html',
                                  {"d": "Device Dist Throughput"}, context)
    if 'ap_client' in request.GET:
        return render_to_response('reports_template/Ap-clients.html',
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
            if not DB.devices.find({"lower_snum": mac.lower()}).count():
                continue
            cursor = DB.devices.find({"lower_snum": mac.lower(), "timestamp" \
                : {"$gt": start_time, "$lt": end_time}})
            

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
        # fetch thdevicedistdevicedistdevicedistdevicedistdevicediste docs
        doc_list = common.let_the_docs_out(post_data)

        get_type = "aps"
        aps = common.calc_type(doc_list, get_type)

        get_type = "clients"
        clients = common.calc_type(doc_list, get_type)

        out_dict = aps

        # join both the dicts
        for times in out_dict:
            if len(clients):
                for client in clients[times]:
                    out_dict[times].append(client)

        # get overall result
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
