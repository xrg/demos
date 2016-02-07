# File: urls.py

from django.conf.urls import include, url
from django.contrib.auth.decorators import login_required
from demos.apps.bds import views
from demos.common.utils import base32cf


urlpatterns = [
    
    url(r'^$', login_required(views.HomeView.as_view()), name='home'),
    
    url(r'^manage/(?:(?P<election_id>[' + base32cf._valid_re + r']+)/)?$', \
        login_required(views.ManageView.as_view()), name='manage'),
]

apipatterns = [
    
    url(r'^setup/(?P<phase>p1|p2)/$', views.ApiSetupView.as_view(), \
        name='setup'),
    
    url(r'^update/$', views.ApiUpdateView.as_view(), name='update'),
]

