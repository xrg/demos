# File: __init__.py

from django.conf import settings

if set(base.DEMOS_APPS).intersection(['ea', 'bds', 'abb']):
    
    import json
    
    from functools import partial
    from kombu.serialization import register
    from demos.common.utils.json import CustomJSONEncoder
    
    register('custom-json', partial(json.dumps, cls=CustomJSONEncoder), \
        json.loads, 'application/x-custom-json', 'utf-8')
    

#eof
