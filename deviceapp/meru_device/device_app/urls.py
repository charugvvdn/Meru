from django.conf.urls import patterns, include, url
from device_app import views, api
from device_app.views import DeviceApplication as dav
#from device_app import pdfgen
#from device_app.pdfgen import ApiBaseClass as pdf_api
from device_app.api_calls import HomeApi, HomeApi2
from device_app.device_report import deviceGraph
from device_app.client_report import clientGraph
deviceapp = dav()

urlpatterns = patterns('',
                       #GET/POST/PUT controller data
                       url(r'^api/auth/hello/$', dav.as_view()),
                       url(r'^api/auth/hello/(?P<mac>([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2}))/$',
                           dav.as_view()),
                       #Client report graph
                       url(r'^report/clientcount/$', clientGraph.as_view()),
                       #Device report graph
                       url(r'^report/devicecount/$', deviceGraph.as_view()),
                       #Dashboard apis
                       url(r'^home/api/$', HomeApi.as_view()),
                       url(r'^home/api2/$', HomeApi2.as_view()),




                       )
