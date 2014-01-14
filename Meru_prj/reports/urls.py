from django.conf.urls import patterns, include, url
from reports import views, api
from reports.api import HomeApi, HomeApi2, DashboardApi, AlarmsApi


urlpatterns = patterns('',
                       url(r'^welcome/$', views.welcome, name='welcome'),
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
                       url(r'^api/', include('devices.urls')),
                       
  




                       )
