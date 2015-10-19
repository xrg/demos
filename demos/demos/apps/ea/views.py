# File: views.py

import random

from base64 import b64encode
from urllib.parse import urljoin, quote

from django import http
from django.db import transaction
from django.core import urlresolvers
from django.utils import translation, timezone
from django.shortcuts import render, redirect
from django.views.generic import View
from django.core.exceptions import ValidationError
from django.core.urlresolvers import reverse

from celery.result import AsyncResult

from demos.apps.ea.forms import ElectionForm, OptionFormSet, \
	PartialQuestionFormSet, BaseQuestionFormSet
from demos.apps.ea.tasks import election_setup, pdf
from demos.apps.ea.models import Config, Election, Task

from demos.common.utils import base32, config, enums
from demos.common.utils.dbsetup import _prep_kwargs


class HomeView(View):
	
	template_name = 'ea/home.html'
	
	def get(self, request):
		return render(request, self.template_name, {})


class CreateView(View):
	
	template_name = 'ea/create.html'
	
	def get(self, request, *args, **kwargs):
		
		election_form = ElectionForm(prefix='election')
		
		# Get an empty question formset
		
		QuestionFormSet = PartialQuestionFormSet(formset=BaseQuestionFormSet)
		question_formset = QuestionFormSet(prefix='question')
		
		question_and_options_list = [(question_formset.empty_form, \
			OptionFormSet(prefix='option__prefix__'))]
		
		context = {
			'election_form': election_form,
			'question_formset': question_formset,
			'question_and_options_list': question_and_options_list,
		}
		
		return render(request, self.template_name, context)

	def post(self, request, *args, **kwargs):
		
		# Get the election form
		
		election_form = ElectionForm(request.POST, prefix='election')
		
		# "Peek" at the number of questions
		
		try:
			questions = int(request.POST['question-TOTAL_FORMS'])
			if questions < 1 or questions > config.MAX_QUESTIONS:
				raise ValueError
		except (ValueError, TypeError, KeyError):
			questions = 0
		
		# Get the list of option formsets, each one corresponds to a question
		
		option_formsets = [OptionFormSet(request.POST, \
			prefix='option' + str(i)) for i in range(questions)]
		
		# Get the question formset
		
		BaseQuestionFormSet1 = type('BaseQuestionFormSet',
			(BaseQuestionFormSet,), dict(option_formsets=option_formsets))
		
		QuestionFormSet = PartialQuestionFormSet(formset=BaseQuestionFormSet1)
		question_formset = QuestionFormSet(request.POST, prefix='question')
		
		# Validate all forms
		
		election_valid = election_form.is_valid()
		question_valid = question_formset.is_valid()
		option_valid = all([formset.is_valid() for formset in option_formsets])
		
		if election_valid and question_valid and option_valid:
			
			election_obj = dict(election_form.cleaned_data)
			
			language = election_obj.pop('language')
			trustee_list = election_obj.pop('trustee_list')
			
			# Pack questions, options and trustees in lists of dictionaries
			
			election_obj['__list_Question__'] = []
			
			for index, (question_form, option_formset) \
				in enumerate(zip(question_formset, option_formsets)):
				
				cleaned_data = question_form.cleaned_data
				
				question_obj = {
					'index': index,
					'text': cleaned_data['question'],
					'columns': cleaned_data['columns'],
					'choices': int(cleaned_data['choices']),
					'__list_OptionC__': [],
				}
				
				for index, option_form in enumerate(option_formset):
					
					option_obj = {
						'index': index,
						'text': option_form.cleaned_data['text'],
					}
					
					question_obj['__list_OptionC__'].append(option_obj)
				election_obj['__list_Question__'].append(question_obj)
			
			election_obj['__list_Trustee__'] = \
				[{'email': email} for email in trustee_list]
			
			# Perform the requested action
			
			if request.is_ajax():
				
				# Create a sample ballot. Since this is not a real ballot,
				# use pseudo-random number generators instead of urandom.
				
				serial = 100
				bytes = config.CREDENTIAL_LEN
				credential = random.getrandbits(bytes * 8).to_bytes(bytes,'big')
				
				ballot_obj = {
					'serial': serial,
					'credential': credential,
					'__list_Part__': [],
				}
				
				for tag in ['A', 'B']:
					
					security_code=base32.random(config.SECURITY_CODE_LEN, False)
					
					part_obj = {
						'tag': tag,
						'vote_token': 'vote-token',
						'security_code': security_code,
						'__list_Question__': [],
					}
					
					for question_obj in election_obj['__list_Question__']:
						
						options = len(question_obj['__list_OptionC__'])
						
						votecode_list = list(range(options))
						random.shuffle(votecode_list)
						
						receipt_list = [base32.random(config.RECEIPT_LEN, False)
							for _ in range(options)]
						
						question_obj = {
							'__list_OptionV__': [],
						}
						
						for votecode,receipt in zip(votecode_list,receipt_list):
							
							data_obj = {
								'votecode': votecode,
								'receipt': receipt,
							}
							
							question_obj['__list_OptionV__'].append(data_obj)
						part_obj['__list_Question__'].append(question_obj)
					ballot_obj['__list_Part__'].append(part_obj)
				election_obj['id'] = 'election-id'
				
				# Temporarily enable the requested language
				
				translation.activate(language)
				
				builder = pdf.BallotBuilder(election_obj)
				pdfbuf = builder.pdfgen(ballot_obj)
					
				translation.deactivate()
				
				# Return the pdf ballot as a base64 encoded string
				
				pdfb64 = b64encode(pdfbuf.getvalue())
				return http.HttpResponse(pdfb64.decode())
			
			else: # Create a new election
				
				with transaction.atomic():
					
					# Atomically get the next election id
					
					config_, created = Config.objects.select_for_update().\
						get_or_create(key='next_election_id')
					
					election_id = config_.value if not created else '0'
					
					config_.value = base32.encode(base32.decode(election_id)+1)
					config_.save(update_fields=['value'])
				
				election_obj['id'] = election_id
				election_obj['state'] = enums.State.PENDING
				
				# Create the new election object
				
				election_kwargs = _prep_kwargs(election_obj, Election)
				election = Election.objects.create(**election_kwargs)
				
				# Prepare and start the election_setup task
				
				task = election_setup.s(election, election_obj, language)
				task.freeze()
				
				Task.objects.create(election_id=election_id, task_id=task.id)
				task.apply_async()
				
				# Redirect to status page
				
				return http.HttpResponseRedirect(urlresolvers.\
					reverse('ea:status', args=[election_id]))
		
		# Add an empty question form and option formset
		
		question_and_options_list = list(zip(question_formset,
			option_formsets)) + [(question_formset.empty_form,
			OptionFormSet(prefix='option__prefix__'))]
		
		question_formset_errors = sum(int(not(question_form.is_valid() and \
			option_formset.is_valid())) for question_form, option_formset \
			in question_and_options_list[:-1])
		
		context = {
			'election_form': election_form,
			'question_formset': question_formset,
			'question_formset_errors': question_formset_errors,
			'question_and_options_list': question_and_options_list,
		}
		
		# Re-display the form with any errors
		return render(request, self.template_name, context, status=422)


class StatusView(View):
	
	template_name = 'ea/status.html'
	
	def get(self, request, *args, **kwargs):
		
		election_id = kwargs.get('election_id')
		
		try:
			normalized = base32.normalize(election_id)
		except (TypeError, ValueError):
			pass
		else:
			if normalized != election_id:
				return redirect('ea:status', election_id=normalized)
			try:
				election = Election.objects.get(id=election_id)
			except Election.DoesNotExist:
				return redirect(reverse('ea:home') + '?error=id')
		
		abb_url = urljoin(config.URL['abb'], quote("results/%s/" % election_id))
		bds_url = urljoin(config.URL['bds'], quote("manage/%s/" % election_id))
		
		context = {
			'abb_url': abb_url,
			'bds_url': bds_url,
			'election': election,
			'State': {state.name: state.value for state in enums.State},
		}
		
		return render(request, self.template_name, context)
	
	def post(self, request, *args, **kwargs):
		
		election_id = kwargs.get('election_id')
		
		if election_id is None:
			return http.HttpResponseNotAllowed(['GET'])
		
		response = {}
		
		try: # Return election creation progress
			
			celery = Task.objects.get(election_id=election_id)
			task = AsyncResult(str(celery.task_id))
			
			response['state'] = enums.State.WORKING.value
			response.update(task.result or {})
		
		except (ValidationError, Task.DoesNotExist):
			
			try: # Return election state or invalid
				
				election = Election.objects.get(id=election_id)
				
				if election.state.value == enums.State.RUNNING.value:
					if timezone.now() < election.start_datetime:
						response['not_started'] = True
					elif timezone.now() > election.end_datetime:
						response['ended'] = True
				
				response['state'] = election.state.value		
			
			except (ValidationError, Election.DoesNotExist):
				return http.HttpResponse(status=422)
		
		return http.JsonResponse(response)


class CenterView(View):
	
	template_name = 'ea/center.html'
	
	def get(self, request):
		pass

