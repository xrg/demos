# File: urls.py

from django.conf.urls import include, url
from django.contrib.auth.decorators import login_required
from demos.apps.vbb import views
from demos.common.utils import base32cf


urlpatterns = [
    
    url(r'^$', views.HomeView.as_view(), name='home'),
    
    url(r'^vote/$', views.VoteView.as_view(), name='vote'),
    
    url(r'^qrcode/$', views.QRCodeScannerView.as_view(), name='qrcode'),
    
    url(r'^(?P<election_id>[' + base32cf._valid_re + r']+)/(?P<vote_token>[' \
        + base32cf._valid_re + r']+)/$', views.VoteView.as_view(), name='vote'),
]

apipatterns = [
    
    url(r'^setup/(?P<phase>p1|p2)/$', views.ApiSetupView.as_view(), \
        name='setup'),
    
    url(r'^update/$', views.ApiUpdateView.as_view(), name='update'),
]

