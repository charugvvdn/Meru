from django.conf.urls import patterns, include, url
from devices.views import DeviceApplication as dav


urlpatterns = patterns('',
                       url(r'^auth/hello/$', dav.as_view()),
                       url(r'^auth/hello/(?P<mac>([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2}))/$',
                           dav.as_view()),
                       
                       
                       )
