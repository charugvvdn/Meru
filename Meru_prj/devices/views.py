from django.http import HttpResponse
from django.db import connections
from django.views.decorators.csrf import csrf_exempt
from pymongo import MongoClient
import datetime
import ast
import json
from django.views.generic.base import View
TIME_INDEX = 60

# Connection with mongoDB client
CLIENT = MongoClient()
DB = CLIENT['nms']

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
        '''config_data = {}
        sec_profile_dict = {"sec-enc-mode": "", "sec-passphrase": "",
                            "sec-profile-name": "", "sec-l2-mode": ""}
        ess_profile_dict = {"ess-profile-name": "", "ess-dataplane-mode": "",
                            "ess-state": "", "ess-ssid-broadcast": "",
                            "ess-security-profile": ""}'''

        cursor = connections['meru_cnms'].cursor()

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
              ASC limit 0 , 1" % str(mac)'''

        query = """SELECT command_json FROM meru_command WHERE \
        `command_mac` = '%s' ORDER BY command_createdon DESC LIMIT 1""" % mac

        cursor.execute(query)
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

        '''if controller.objects.filter(mac_address=mac).exists():
            self.true_response["mac"] = mac
            return HttpResponse(json.dumps(self.true_response))'''

        query = "SELECT COUNT(1) FROM meru_controller WHERE \
        `controller_mac` = '%s'" % mac
        cursor = connections['meru_cnms'].cursor()
        cursor.execute(query)
        result = cursor.fetchall()
        if not result[0][0]:
            self.false_response["status"] = "false"
            self.false_response["mac"] = mac
            return HttpResponse(json.dumps(self.false_response))
        self.true_response["status"] = "true"
        self.true_response["mac"] = mac
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
        post_data = json.loads(request.body)

        if 'snum' in post_data.keys():
            mac = post_data.get('snum')
        else:
            mac = post_data.get('controller')

        no_mac = {"status": "false", "mac": mac}

        '''if not controller.objects.filter(mac_address=mac).exists():
            return HttpResponse(json.dumps(no_mac))'''

        query = "SELECT COUNT(1) FROM meru_controller WHERE \
        `controller_mac` = '%s'" % mac
        cursor = connections['meru_cnms'].cursor()
        cursor.execute(query)
        result = cursor.fetchall()
        if not result[0][0]:
            return HttpResponse(json.dumps(no_mac))

        utc_1970 = datetime.datetime(1970, 1, 1)
        utcnow = datetime.datetime.utcnow()
        timestamp = int((utcnow - utc_1970).total_seconds())

        post_data['timestamp'] = timestamp
        post_data['lower_snum'] = mac.lower()
        self.type_casting(post_data)
        

        DB.devices.insert(post_data)

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

        self.true_response["mac"] = mac
        self.false_response["mac"] = mac
        self.false_response["status"] = "false"

        query = "SELECT COUNT(1) FROM meru_controller WHERE \
        `controller_mac` = '%s'" % mac
        cursor = connections['meru_cnms'].cursor()
        cursor.execute(query)
        result = cursor.fetchall()
        if not result[0][0]:
            return HttpResponse(json.dumps(self.false_response))

        try:
            query = """ UPDATE meru_command SET command_status = 2 WHERE \
                    command_mac = '%s'""" % mac
            cursor = connections['meru_cnms'].cursor()
            cursor.execute(query)
            return HttpResponse(json.dumps(self.true_response))

        except Exception as error:
            
            return HttpResponse(json.dumps(self.false_response))

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
                client['apId'] = int(client['apId']) if str(client['apId']).\
                isdigit() else 0
                client['rxBytes'] = int(client['rxBytes']) \
                if str(client['rxBytes']).isdigit() else 0
                client['txBytes'] = int(client['txBytes']) \
                if str(client['txBytes']).isdigit() else 0
                client['txBytes'] = int(client['txBytes']) \
                if str(client['txBytes']).isdigit() else 0

        return doc