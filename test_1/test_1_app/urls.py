from django.conf.urls import patterns, include, url
from test_1_app import views


urlpatterns = patterns('',
	url(r'^api/auth/hello/$', views.gHello, name='hello'),
	url(r'^api/auth/hello/update/$', views.uHello, name='uHello'),
	url(r'^api/auth/hello/mon/$', views.cHello, name='cHello'),
	url(r'^reports/stationThroughput/$', views.clientThroughput),
)

