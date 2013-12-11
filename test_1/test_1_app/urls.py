from django.conf.urls import patterns, include, url
from test_1_app import views
from test_1_app.views import DeviceApplication as dav


urlpatterns = patterns('',
                       url(r'^welcome/$', views.Welcome, name='welcome'),
                       # url(r'^api/auth/hello/$', views.gHello, name='hello'),
                       # url(r'^api/auth/hello/([0-9A-F]{2}[:-]){5}([0-9A-F]{2})/$', views.uHello, name='uHello'),
                       # url(r'^api/auth/hello/mon/$', views.cHello, name='cHello'),
                       url(r'^api/auth/hello/$', dav.as_view()),
                       # url(r'^api/auth/hello/(?P<mac=>[0-9A-F]{2}[:-]){5}([0-9A-F]{2})/$', dav.as_view()),
                       url(r'^api/auth/hello/(?P<mac>([0-9A-F]{2}[:-]){5}([0-9A-F]{2}))/$', dav.as_view()),
                       # url(r'^api/auth/hello/([0-9A-F]{2}[:-]){5}([0-9A-F]{2})/$', views.uHello, name='uHello'),
                       url(r'^reports/stationThroughput/$', views.clientThroughput),
                       url(r'^reports/APThroughput/$', views.APThroughput),
                       url(r'^reports/wifiexp/$', views.WifiExperience),
                       url(r'^reports/overallThroughput/$', views.OverallThroughput),
)

