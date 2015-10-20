# File: views.py

import json
import math
import hashlib
import logging

from base64 import b64encode
try:
    from itertools import zip_longest
except ImportError:
    from itertools import izip_longest as zip_longest

from collections import OrderedDict

from google.protobuf import message

from django import http
from django.db import transaction
from django.apps import apps
from django.conf.urls import include, url
from django.shortcuts import get_object_or_404, redirect, render
from django.middleware import csrf
from django.views.generic import View
from django.db.models.query import QuerySet
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.utils.decorators import method_decorator
from django.core.urlresolvers import reverse
from django.core.serializers.json import DjangoJSONEncoder

from demos.apps.abb.models import Election, Question, Ballot, Part, \
	OptionV, OptionC

from demos.common.utils import api, base32, config, dbsetup, protobuf
from demos.common.utils.permutation import permute_ori

logger = logging.getLogger(__name__)
app_config = apps.get_app_config('abb')


class HomeView(View):
	
	template_name = 'abb/home.html'
	
	def get(self, request):
		return render(request, self.template_name, {})


class AuditView(View):
	
	template_name = 'abb/audit.html'
	
	def get(self, request, *args, **kwargs):
		
		election_id = kwargs.get('election_id')
		
		try:
			normalized = base32.normalize(election_id)
		except (TypeError, ValueError):
			pass
		else:
			if normalized != election_id:
				return redirect('abb:audit', election_id=normalized)
			try:
				election = Election.objects.get(id=election_id)
			except Election.DoesNotExist:
				return redirect(reverse('abb:home') + '?error=id')
			else:
				questions = Question.objects.filter(election=election)
		
		participants = Ballot.objects.filter(election=election, \
			part__optionv__voted=True).distinct().count() if election else 0
		
		context = {
			'election': election,
			'questions': questions,
			'participants': str(participants),
		}
		
		return render(request, self.template_name, context)
	
	def post(self, request, *args, **kwargs):
		
		election_id = kwargs.get('election_id')
		
		if election_id is None:
			return http.HttpResponseNotAllowed(['GET'])
		
		try:
			serial = int(request.POST.get('serial'))
		except ValueError:
			return http.HttpResponse(status=422)
		
		try:
			election = Election.objects.get(id=election_id)
			ballot = Ballot.objects.get(election=election, serial=serial)
			part_qs = Part.objects.filter(ballot=ballot);
			question_qs = Question.objects.filter(election=election);
			
			# 
			
			url_kwargs = {
				'Election__id': election.id,
				'Ballot__serial': ballot.serial,
			}
			
			url = reverse('api:export:election:ballot:get', kwargs=url_kwargs)
			
			# 
			
			vote = None
			
			# 
			
			parts = []
			
			for p in part_qs:
				
				questions = []
				
				for q in question_qs:
					
					optionv_qs = OptionV.objects.filter(part=p, question=q)
					options = list(optionv_qs.values_list('index','votecode','voted'))
					
					if p.security_code:
						
						vote = 'A' if p.tag != 'A' else 'B'
						
						int_ = base32.decode(p.security_code) + q.index
						bytes_ = math.ceil(int_.bit_length() / 8)
						value = hashlib.sha256(int_.to_bytes(bytes_, 'big'))
						index = int.from_bytes(value.digest(), 'big')
						
						options = permute_ori(options, index)
					
					questions.append((q.index, options))
				
				parts.append((p.tag, questions))
			
			# 
			
			response = {
				'url': url,
				'vote': vote,
				'parts': parts,
			}
		
		except (ValidationError, ObjectDoesNotExist):
			return http.HttpResponse(status=422)
		
		return http.JsonResponse(response)


class ResultsView(View):
	
	template_name = 'abb/results.html'
	
	def get(self, request, *args, **kwargs):
		return render(request, self.template_name, {})


class SetupView(View):
	
	@method_decorator(api.user_required('ea'))
	def dispatch(self, *args, **kwargs):
		return super(SetupView, self).dispatch(*args, **kwargs)
	
	def get(self, request):
		csrf.get_token(request)
		return http.HttpResponse()
	
	def post(self, request, *args, **kwargs):
		
		try:
			task = request.POST['task']
			election_obj = json.loads(request.POST['payload'])
			
			if task == 'election':
				dbsetup.election(election_obj, app_config)
			elif task == 'ballot':
				dbsetup.ballot(election_obj, app_config)
			else:
				raise Exception('SetupView: Invalid POST task: %s' % task)
		except Exception:
			logger.exception('SetupView: API error')
			return http.HttpResponse(status=422)
		
		return http.HttpResponse()


class UpdateView(View):
	
	@method_decorator(api.user_required('ea'))
	def dispatch(self, *args, **kwargs):
		return super(UpdateView, self).dispatch(*args, **kwargs)
	
	def get(self, request):
		csrf.get_token(request)
		return http.HttpResponse()
	
	def post(self, request, *args, **kwargs):
		
		try:
			data = json.loads(request.POST['data'])
			model = app_config.get_model(data['model'])
			
			fields = data['fields']
			natural_key = data['natural_key']
			
			obj = model.objects.get_by_natural_key(**natural_key)
			
			for name, value in fields.items():
				setattr(obj, name, value)
			
			obj.save(update_fields=list(fields.keys()))
		
		except Exception:
			logger.exception('UpdateView: API error')
			return http.HttpResponse(status=422)
		
		return http.HttpResponse()


class VoteView(View):
	
	@method_decorator(api.user_required('vbb'))
	def dispatch(self, *args, **kwargs):
		return super(VoteView, self).dispatch( *args, **kwargs)
	
	def get(self, request):
		csrf.get_token(request)
		return http.HttpResponse()
	
	def post(self, request, *args, **kwargs):
		
		try:
			votedata = json.loads(request.POST['votedata'])
			
			part1_votecodes = votedata['part1_votecodes']
			part1_natural_key = votedata['part1_natural_key']
			part2_security_code = votedata['part2_security_code']
			
			part1 = Part.objects.get_by_natural_key(**part1_natural_key)
			part2 = Part.objects.exclude(tag=part1.tag).\
				get(ballot=part1.ballot)
			
			election_id = part1_natural_key['id']
			question_qs = Question.objects.filter(election__id=election_id)
			
			# Verify vote's correctness and save it to the db in an atomic
			# transaction. If anything fails, rollback and return an error.
			
			with transaction.atomic():
				for question, vc_list \
					in zip_longest(question_qs, part1_votecodes):
					
					vc_len = len(vc_list)
					
					if vc_len < 1 or vc_len > question.choices:
						raise ValueError('VoteView: votecodes error')
					
					optionv_qs = OptionV.objects.filter(part=part1,
						question=question, votecode__in=vc_list)
					
					if vc_len != optionv_qs.count():
						raise ValueError('VoteView: votecodes error')
					
					optionv_qs.update(voted=True)
				
				part2.security_code = part2_security_code
				part2.save(update_fields=['security_code'])
		
		except Exception:
			logger.exception('VoteView: API error')
			return http.HttpResponse(status=422)
		
		return http.HttpResponse()


class ExportView(View):
	
	template_name = 'abb/export.html'
	
	_urlinfo = OrderedDict([
		('election', {
			'fields': [],
			'args': [('id', '[a-zA-Z0-9]+')],
			'model': Election,
		}),
		('ballot', {
			'fields': [],
			'args': [('serial', '[0-9]+')],
			'model': Ballot,
		}),
		('part', {
			'fields': [],
			'args': [('tag', '[AaBb]')],
			'model': Part,
		}),
		('question', {
			'fields': ['key'],
			'args': [('index', '[0-9]+')],
			'model': Question,
		}),
		('option', {
			'fields': ['com', 'zk1', 'zk2'],
			'args': [('index', '[0-9]+')],
			'model': OptionV,
		}),
	])
	
	@staticmethod
	def urlpatterns():
		
		urlpatterns = []
		
		for ns, data in reversed(list(ExportView._urlinfo.items())):
			
			model = data['model']
			
			arg_path = '/'.join(['(?P<' + model.__name__ + '__' + \
				field + '>' + regex + ')' for field, regex in data['args']])
			
			urlpatterns = [url(r'^' + ns + 's/', include([
				url(r'^$', ExportView.as_view(), name='list'),
				url(r'^' + arg_path + '/', include([
					url(r'^$', ExportView.as_view(), name='get'),
				] + urlpatterns)),
			], namespace=ns))]
		
		return urlpatterns
		
	
	def get(self, request, **kwargs):
		
		namespace = request.resolver_match.namespaces[-1]
		
		ns_list = list(self._urlinfo.items())
		i = list(self._urlinfo.keys()).index(namespace)
		
		# Accept case insensitive ballot part tags
		
		if 'Part__tag' in kwargs:
			kwargs['Part__tag'] = kwargs['Part__tag'].upper()
		
		# Arrange input arguments by namespace
		
		kwkeys = {}
		
		for key, value in kwargs.items():
			
			try:
				model, field = key.split('__', maxsplit=1)
			except ValueError:
				continue
			else:
				kwkeys.setdefault(model, {}).update({field: value})
		
		# Parse all namespaces up to the requested one (excluding)
		
		objects = {}
		
		for ns, data in ns_list[:i+1]:
			
			model = data['model']
			
			kwflds = {f.name: objects[k] for k in objects for f
				in model._meta.get_fields() if f.is_relation
				and k == f.related_model.__name__}
			
			kwflds.update(kwkeys.get(model.__name__) or {})
			
			if ns != namespace:
				objects[model.__name__] = get_object_or_404(model, **kwflds)
		
		# Perform the requested action
		
		if request.resolver_match.url_name == 'get':
			
			def _build_data(i, objects, kwflds):
				
				ns, data = ns_list[i]
				objects = objects.copy()
				
				model = data['model']
				
				# Output fields is the intersection of the url query string's
				# fields and the namespace's fields
				
				f1 = data['fields']
				f2 = [s for q in request.GET.getlist(ns, ['']) \
					for s in q.split(',') if s]
				
				fields = (set(f1) & set(f2)) if f2 else f1
				
				# Update input query's fields with the model's related fields
				
				kwflds.update({f.name: objects[k] for k in objects for f
					in model._meta.get_fields() if f.is_relation
					and k == f.related_model.__name__})
				
				# Get all namespace objects as dictionaries (possibly empty)
				
				obj_qs = model.objects.filter(**kwflds)
				
				if not obj_qs:
					raise http.Http404('No ' + \
						model.__name__ + ' matches the given query.')
				
				values = list(obj_qs.values(*fields)) \
					if fields else [dict() for _ in range(obj_qs.count())]
				
				# Repeat for every sub-namespace (if any)
				
				if i+1 < len(ns_list):
					for obj, value in zip(obj_qs, values):
						
						ns_next = ns_list[i+1][0]
						objects[model.__name__] = obj
						
						value[ns_next] = _build_data(i+1, objects, {})
				
				return values
			
			# Return the requested model's dictionary
			
			data = _build_data(i, objects, kwflds)[0]
			
		elif request.resolver_match.url_name == 'list':
			
			# Return the list of available input arguments
			
			args = [arg[0] for arg in data['args']]
			flat = len(args) == 1
			
			object_qs = model.objects.filter(**kwflds)
			data = list(object_qs.values_list(*args, flat=flat))
		
		# Serialize and return the structure
		
		if 'file' in request.GET:
			response = http.HttpResponse(content_type='application/json')
			fn = ns + ('s' if request.resolver_match.url_name == 'list' else '')
			response['Content-Disposition']='attachment; filename="'+fn+'.json"'
			json.dump(data, response, indent=4, sort_keys=True, cls=JSONEncoder)
		
		elif request.is_ajax():
			response = http.JsonResponse(data, safe=False, encoder=JSONEncoder)
		
		else:
			text = json.dumps(data, indent=4, sort_keys=True, cls=JSONEncoder)
			response = render(request, self.template_name, {'text': text})
		
		return response


class JSONEncoder(DjangoJSONEncoder):
	"""JSONEncoder subclass that supports date/time and protobuf types."""
	
	def default(self, o):
		
		if isinstance(o, message.Message):
			return protobuf.to_dict(o, ordered=True)
		
		return super(JSONEncoder, self).default(o)

