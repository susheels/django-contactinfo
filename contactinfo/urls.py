from django.conf.urls.defaults import *
from django.contrib.auth import views as auth_views

import contactinfo.views as views

urlpatterns = patterns('',
    
    url(r'^location/create/$', views.create_edit_location, name='create_location'),
    url(r'^country/(?P<country_iso>\w+)/address_form_html/$', views.get_address_form_html, name='get_address_form_html'),

)
