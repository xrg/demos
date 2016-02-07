# File: __init__.py

import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'demos.settings')

from django.conf import settings

if set(settings.DEMOS_APPS).intersection(['ea', 'bds', 'abb']):
    
    import json
    
    from functools import partial
    from kombu.serialization import register
    from demos.common.utils.json import CustomJSONEncoder
    
    register('custom-json', partial(json.dumps, cls=CustomJSONEncoder), \
        json.loads, 'application/x-custom-json', 'utf-8')
    
    from .celeryapp import app as celery_app

#eof
