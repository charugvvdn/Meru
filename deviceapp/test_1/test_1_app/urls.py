from django.conf.urls import patterns, include, url
from test_1_app import views, api
from test_1_app.views import DeviceApplication as dav
from test_1_app import pdfgen
from test_1_app.api_calls import HomeApi, HomeApi2, DashboardApi, AlarmsApi

deviceapp = dav()

urlpatterns = patterns('',
                       url(r'^welcome/$', views.welcome, name='welcome'),
                       # url(r'^api/auth/hello/$', views.gHello, name='hello'),
                       # url(r'^api/auth/hello/([0-9A-F]{2}[:-]){5}([0-9A-F]{2})/$', views.uHello, name='uHello'),
                       # url(r'^api/auth/hello/mon/$', views.cHello, name='cHello'),
                       url(r'^api/auth/hello/$', dav.as_view()),
                       # url(r'^api/auth/hello/(?P<mac=>[0-9A-F]{2}[:-]){5}([0-9A-F]{2})/$', dav.as_view()),
                       url(r'^api/auth/hello/(?P<mac>([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2}))/$',
                           dav.as_view()),
                       # url(r'^api/auth/hello/([0-9A-F]{2}[:-]){5}([0-9A-F]{2})/$', views.uHello, name='uHello'),
                       url(r'^reports/stationThroughput/$',
                           views.client_throughput),
                       url(r'^reports/APThroughput/$', views.ap_throughput),
                       url(r'^reports/wifi_experience/$',
                           views.wifi_experience),
                       url(r'^reports/overall_throughput/$',
                           views.overall_throughput),
                       url(r'^reports/devicedist/$', views.devicetype),
                       url(r'^reports/ap_clients/$', views.ap_clients),
                       url(r'^home/api/$', HomeApi.as_view()),
                       url(r'^home/api2/$', HomeApi2.as_view()),
                       url(r'^dashboard/api/$', DashboardApi.as_view()),
                       url(r'^alarms/api/$', AlarmsApi.as_view()),
                       url(r'^report-gen/$', pdfgen.main_view),
                       url(r'^send-mail/$', pdfgen.send_mail),




                       )
