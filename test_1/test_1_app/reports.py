from pymongo import MongoClient
import datetime
import json
import ast

# Connection with mongoDB client
CLIENT = MongoClient()
DB = CLIENT['nms']
UTC_1970 = datetime.datetime(1970, 1, 1)
UTC_NOW = datetime.datetime.utcnow()
OFFSET = UTC_NOW - datetime.timedelta(minutes=30)
class ClientReport():

    '''Common variable used under the class methods'''
    def __init__(self,**kwargs):
        self.lt= kwargs['lt']
        self.gt = kwargs['gt']
        self.doc_list = []
        self.cursor = DB.devices.find({"timestamp" : {"$gt":self.lt , "$lt":self.gt }})
        

    
    def busiestClients(self, **kwargs ):
        '''Calculating top 10 busiest clients '''
        typeof = 'clients'
        result_list = []
        usage = 0
        doc_list = []
        for doc in self.cursor:
            doc_list.append(doc)
        for doc in doc_list:
            if 'msgBody' in doc and 'controller' in doc['msgBody']:
                if typeof in doc['msgBody'].get('controller'):
                    # get clients
                    
                    clients = doc.get('msgBody').get('controller').get(typeof)
                    unique_clients = {}
                    
                    for client in clients:
                        if client["mac"] not in unique_clients:
                            usage = client['rxBytes']+client['txBytes']
                            unique_clients[client["mac"]] = 0
                            result_list.append([client['mac'],usage])
        print result_list
        return result_list
def main():
    obj = ClientReport(lt=1392871841,gt=1392871845)
    obj.busiestClients()

if __name__ == "__main__":
        main()

'''class Client_report(View):

    lient Report generation

    def get(self, request):
        Client report Generation
        response_list = []
        response = {}
        obj = ClientReport()
        reporttype = ''
        if 'reporttype' in request.GET:
            reporttype = int(request.GET.get('reporttype'))
        if reporttype == "busiestclient":
            result = obj.busiestClients()
            print result
        
        return response'''