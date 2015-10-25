# File: urls.py

"""demos URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.8/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Add an import:  from blog import urls as blog_urls
    2. Add a URL to urlpatterns:  url(r'^blog/', include(blog_urls))
"""

from importlib import import_module

from django.conf import settings
from django.conf.urls import include, url
from django.conf.urls.i18n import i18n_patterns
from django.contrib import admin

urlpatterns = []

if 'django_cas' in settings.INSTALLED_APPS:
    urlpatterns += [url(r'^cas/login/$', 'django_cas.views.login', name='cas_login'),
                    url(r'^cas/logout/$', 'django_cas.views.logout') ]

for iapp in settings.DEMOS_APPS:
    urlconfig = import_module('demos.apps.%s.urls' % iapp)
    durl = '^' + ((iapp + '/') if len(settings.DEMOS_APPS) > 1 else '')
    urlpatterns += i18n_patterns(url(durl, include(urlconfig, namespace=iapp, app_name=iapp))) + \
        [url(durl + 'api/', include(urlconfig.apipatterns, namespace=iapp+'-api', app_name=iapp))]

#eof

