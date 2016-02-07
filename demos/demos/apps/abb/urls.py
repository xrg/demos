# File: urls.py

from django.conf.urls import include, url
from django.views.generic import RedirectView
from django.contrib.auth.decorators import login_required
from demos.apps.abb import views
from demos.common.utils import base32cf


urlpatterns = [
    url(r'^$', views.HomeView.as_view(), name='home'),
    url(r'^(?P<election_id>[' + base32cf._valid_re + r']+)/$', RedirectView.as_view(pattern_name='abb:results', permanent=True)),
    url(r'^audit/(?:(?P<election_id>[' + base32cf._valid_re + r']+)/)?$', \
        views.AuditView.as_view(), name='audit'),
    url(r'^results/(?:(?P<election_id>[' + base32cf._valid_re + r']+)/)?$', \
        views.ResultsView.as_view(), name='results'),
]

apipatterns = [
    url(r'^setup/(?P<phase>p1|p2)/$', views.ApiSetupView.as_view(), \
        name='setup'),
    url(r'^update/$', views.ApiUpdateView.as_view(), name='update'),
    url(r'^vote/$', views.ApiVoteView.as_view(), name='vote'),
    url(r'^export/', include(views.ApiExportView.as_patterns(), \
        namespace='export')),
]

