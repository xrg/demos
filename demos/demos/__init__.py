# File: __init__.py

import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'demos.settings')

from django.conf import settings

if set(settings.DEMOS_APPS).intersection(['ea', 'bds', 'abb']):
    from .celeryapp import app as celery_app

#eof
