from django.http import HttpResponse
from django.db import connection, transaction
from django.views.decorators.csrf import csrf_protect
from django.db.models import Q
from pymongo import MongoClient
from datetime import datetime
import ast
import json

from test_1_app.models import controller, command, alarm, dashboard_info, ssid, security_profile, ssid_in_command

#Connection with mongodb client
client = MongoClient()
db = client['nms']

'''
	To check whether specified mac has registered with the mac or not,
	performing is_registered	
'''
def gHello(request):
	mac = request.GET.get('mac')
	false_response = { "status" : "false", "mac" : mac}
	true_response = { "status" : "true", "mac" : mac}

	if 'snum' in request.GET.keys():
		mac = request.GET.get('snum')

	if controller.objects.filter(mac_address=mac).exists():
		return HttpResponse(json.dumps(true_response))

	return HttpResponse(json.dumps(false_response))

'''
	Update from the controller with info that all the commands has 
	been successfully executed on that controller
'''
def uHello(request):
	mac = request.GET.get('mac')
	false_response = {"status" : "false", "mac" : mac}	
	true_response  = {"status" : "true", "mac" : mac}
	null_mac = {"status" : "Null mac"}
	not_registered = {"status" : "not registered"}

	if mac == "":
		return HttpResponse(json.dumps(null_mac))

	if not controller.objects.filter(mac_address=mac).exists():
		return HttpResponse(json.dumps(false_response))
	else:
		flag = 2

	query_dict = command.objects.filter(
			Q(controller_mac_address=mac, flag=0) | Q(controller_mac_address=mac, flag=1)
		).values('command_id', 'flag')
	
#	print query_dict[0]
	''' 
	Should we check for len(query_dict == 0) ??
	This query would return a single or multiple results ?
	'''	

	if 'command_id' in query_dict[0]:
		command.objects.filter(command_id=query_dict[0]['command_id']).update(flag=flag)
	else:
		return HttpResponse(json.dumps(false_response))

	return HttpResponse(json.dumps(true_response))

def getMacId(mac):
	if mac == "":
		return False 

	query_dict = controller.objects.filter(mac_address=mac).values('cid')	

	if 'cid' in query_dict[0]:
		return query_dict[0]

	return "No Mac"

'''
	Request:  Monitoring data from controller and insert that data into
	a mongodb data source.
	Response: Respond with commands for the controller that has been registered
	by a user for that particular controller
'''
def cHello(request):
	post_data = ast.literal_eval(request.POST.lists()[0][0])
#	mac = post_data['mac']
	print post_data
#	print mac

	ap_info = {"total" : 0, "up" : 0, "down" : 0}	
	client_info = {"total" : 0, "up" : 0, "down" : 0}
	alarm_info = {"total" : 0}
	
	if 'snum' in post_data.keys():
		mac = post_data.get('snum')
	else:
		mac = post_data.get('controller')

	if not controller.objects.filter(mac_address=mac).exists():
		return HttpResponse(json.dumps(no_mac))


	if 'type' in post_data.keys():
		if post_data.get('type') == 'controller':
			controller_dict = post_data.get('controller')
			print type(controller_dict)
			db.controllers.insert(controller_dict)

		if post_data.get('type') == 'alarms':
			alarm_list = post_data.get('alarms')
			for alarm in alarm_list:
				alarm_info["total"] += 1
				db.alarms.insert(alarm)

		if post_data.get('type') == 'aps':
			ap_list = post_data.get('aps')
			for ap in ap_list:
				if ap["status"].lower() == "disabled":
					ap_info["down"] += 1
				else:
					ap_info["up"] += 1
			ap_info["total"] += 1
			db.aps.insert(ap)

		if post_data.get('type') == 'clients':
			client_list = post_data.get('clients')
			for client in client_list:
				if client["status"].lower() == "associated":
					client_info["up"] += 1
				else:
					client_info["down"] += 1
			client_info["total"] += 1	
			db.clients.insert(client)
	else:
		controller_doc = post_data.get('msgBody').get('controller')
		db.controllers.insert(controller_doc)

		if 'alarms' in post_data.get('msgBody').get('controller'):
			alarm_list = post_data.get('msgBody').get('controller').get('alarms')
			for alarm in alarm_list:
				alarm_info["total"] += 1
				db.alarms.insert(alarm)

		if 'aps' in post_data.get('msgBody').get('controller'):
			ap_list = post_data.get('msgBody').get('controller').get('aps')
			for ap in ap_list:
				if ap["status"].lower() == "disabled":
					ap_info["down"] += 1
				else:
					ap_info["up"] += 1
				ap_info["total"] += 1
				db.aps.insert(ap)

		if 'clients' in post_data.get('msgBody').get('controller'):
                        client_list = post_data.get('msgBody').get('controller').get('clients')
                        for client in client_list:
				if client["status"].lower() == "associated":
					client_info["up"] += 1
				else:
					client_info["down"] += 1
				client_info["total"] += 1
                                db.clients.insert(client)

	utc_1970 = datetime(1970, 1, 1)
	utcnow = datetime.utcnow()
	timestamp = int((utcnow - utc_1970).total_seconds())

	cursor = connection.cursor()
	cursor.execute("INSERT INTO test_1_app_dashboard_info (controller_mac, client_info, ap_info, alarm_info, \
		ap_up, ap_down, client_up, client_down, updated_on) VALUE ('%s', %s, %s, %s, %s, %s, %s, %s, %s)" \
		% (str(mac), client_info["total"], ap_info["total"], alarm_info["total"], ap_info["up"], ap_info["down"], \
		client_info["up"], client_info["down"], timestamp))

	transaction.commit_unless_managed()

	config_data = isConfigData(mac)

	return HttpResponse(json.dumps(config_data))

'''
	Generating the commands for the controller with
	given controller mac address passed as `mac`
'''
def isConfigData(mac):
	config_data = {}
	sec_profile_dict = {"sec-enc-mode":"", "sec-passphrase":"", "sec-profile-name":"", "sec-l2-mode":""}
	ess_profile_dict = {"ess-profile-name":"", "ess-dataplane-mode":"", "ess-state":"", "ess-ssid-broadcast":"", "ess-security-profile":""}
	
	cursor = connection.cursor()
	
	q = "SELECT test_1_app_ssid.ssid,test_1_app_security_profile.security_profile_id ,test_1_app_security_profile.enc_mode as\
		'sec-enc-mode',test_1_app_security_profile.passphrase as 'sec-passphrase',test_1_app_security_profile.profile_name as\
		'sec-profile-name',test_1_app_security_profile.l2_mode as 'sec-l2-mode',`test_1_app_ssid`.name as 'ess-profile-name',\
		`test_1_app_ssid`.dataplane_mode as 'ess-dataplane-mode',`test_1_app_ssid`.enabled as 'ess-state',\
		`test_1_app_ssid`.visible as 'ess-ssid-broadcast',`test_1_app_security_profile`.profile_name as\
		'ess-security-profile' FROM  `test_1_app_ssid`\
                LEFT JOIN\
         `test_1_app_security_profile` ON (test_1_app_security_profile.security_profile_id=`test_1_app_ssid`.security_profile_id)\
         INNER JOIN test_1_app_ssid_in_command ON (test_1_app_ssid_in_command.ssid=`test_1_app_ssid`.ssid)\
         INNER JOIN test_1_app_command ON (test_1_app_ssid_in_command.command_id=`test_1_app_command`.command_id)\
          WHERE `test_1_app_command`.`controller_mac_address` = '%s'  and (`test_1_app_command`.flag='0' or `test_1_app_command`.flag='1')\
         ORDER BY  `test_1_app_command`.`timestamp`  ASC limit 0,1" % str(mac)

	cursor.execute(q)
	result = cursor.fetchall()
	
	if len(result) != 0:
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
		return []

	return config_data

