# File: masks.py

import re

_masks = {
 	
 	'bds' : {
	 	'Election': ['id', 'title', 'ballots', 'start_datetime', \
	 		'end_datetime', 'state'],
	 	'Trustee': ['email'],
	 	'Ballot': ['serial'],
	 	'Part': ['tag', 'security_code', 'vote_token'],
	 },
 	
 	'abb' : {
	 	'Election': ['id', 'title', 'ballots', 'start_datetime', \
	 		'end_datetime', 'state'],
	 	'Question': ['text', 'key', 'index', 'choices'],
	 	'OptionC': ['text', 'index'],
	 	'Ballot': ['serial'],
	 	'Part': ['tag'],
	 	'OptionV' : ['votecode', 'com', 'zk1', 'index', 'question'],
	 },
 	
 	'vbb' : {
	 	'Election': ['id', 'title', 'ballots', 'start_datetime', \
	 		'end_datetime', 'state'],
	 	'Question': ['text', 'index', 'columns', 'choices'],
	 	'OptionC': ['text', 'index'],
	 	'Ballot': ['serial', 'credential_hash'],
	 	'Part': ['tag', 'security_code_hash'],
	 	'OptionV' : ['votecode', 'receipt', 'index', 'question'],
	 },
}


def _apply_mask(obj, app_mask, model_mask):
	
	result = {}
	
	for key, value in obj.items():
		
		if key in model_mask:
			result[key] = value
		
		else:
			match = re.search('^__list_(.+)__$', key)
			if match:
				model = match.group(1)
				if model in app_mask:
					result[key] = [_apply_mask(_obj, app_mask, \
						app_mask[model]) for _obj in value]
	
	return result


def apply_mask(app, obj, model='Election'):
	return _apply_mask(obj, _masks[app], _masks[app][model])

