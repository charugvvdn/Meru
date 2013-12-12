from django.conf.urls import patterns, include, url
from test_1_app import views
from test_1_app.views import DeviceApplication as dav


urlpatterns = patterns('',
                        url(r'^welcome/$', views.welcome, name='welcome'),
                        # url(r'^api/auth/hello/$', views.gHello, name='hello'),
                        # url(r'^api/auth/hello/([0-9A-F]{2}[:-]){5}([0-9A-F]{2})/$', views.uHello, name='uHello'),
                        # url(r'^api/auth/hello/mon/$', views.cHello, name='cHello'),
                        url(r'^api/auth/hello/$', dav.as_view()),
                        # url(r'^api/auth/hello/(?P<mac=>[0-9A-F]{2}[:-]){5}([0-9A-F]{2})/$', dav.as_view()),
                        url(r'^api/auth/hello/(?P<mac>([0-9A-F]{2}[:-]){5}([0-9A-F]{2}))/$', dav.as_view()),
                        # url(r'^api/auth/hello/([0-9A-F]{2}[:-]){5}([0-9A-F]{2})/$', views.uHello, name='uHello'),
                        url(r'^reports/stationThroughput/$', views.client_throughput),
                        url(r'^reports/APThroughput/$', views.ap_throughput),
                        url(r'^reports/wifiexp/$', views.wifi_experience),
                        url(r'^reports/overallThroughput/$', views.overall_throughput),
                        url(r'^reports/devicedist/$', views.devicetype),
)