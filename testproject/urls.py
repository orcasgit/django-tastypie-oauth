from django.conf.urls import patterns, include
from polls.api import api


urlpatterns = patterns('', (r'^api/', include(api.urls)))
