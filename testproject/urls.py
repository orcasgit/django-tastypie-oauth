from django.conf.urls import include, url
from polls.api import api


urlpatterns = [url(r'^api/', include(api.urls))]
