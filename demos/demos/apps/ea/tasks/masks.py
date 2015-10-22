# File: masks.py

import re

_masks = {
    
    'bds' : {
        'Election': ['id', 'title', 'start_datetime', 'end_datetime', \
            'long_votecodes', 'state'],
        'Trustee': ['email'],
        'Ballot': ['serial'],
        'Part': ['tag', 'security_code', 'vote_token'],
     },
    
    'abb' : {
        'Election': ['id', 'title', 'start_datetime', 'end_datetime', \
            'long_votecodes', 'state', 'ballots'],
        'Question': ['text', 'key', 'index', 'choices'],
        'OptionC': ['text', 'index'],
        'Ballot': ['serial', 'credential_hash'],
        'Part': ['tag', 'security_code_hash2'],
        'OptionV' : ['votecode', 'long_votecode_hash', 'com', 'zk1', 'index',
            'question'],
     },
    
    'vbb' : {
        'Election': ['id', 'title', 'start_datetime', 'end_datetime', \
            'long_votecodes', 'state', 'ballots'],
        'Question': ['text', 'index', 'columns', 'choices'],
        'OptionC': ['text', 'index'],
        'Ballot': ['serial', 'credential_hash'],
        'Part': ['tag', 'security_code_hash2'],
        'OptionV' : ['votecode', 'long_votecode_hash', 'receipt', 'index',
            'question'],
     },
}

_mask_list_re = re.compile('^__list_(.+)__$')


def _apply_mask(obj, app_mask, model_mask):
    
    result = {}
    
    for key, value in obj.items():
        
        if key in model_mask:
            result[key] = value
        
        else:
            match = _mask_list_re.search(key)
            if match:
                model = match.group(1)
                if model in app_mask:
                    result[key] = [_apply_mask(_obj, app_mask, \
                        app_mask[model]) for _obj in value]
    
    return result


def apply_mask(app, obj, model='Election'):
    return _apply_mask(obj, _masks[app], _masks[app][model])

