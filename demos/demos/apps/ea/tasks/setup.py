# File: setup.py

import io
import os
import hmac
import json
import math
import time
import random
import hashlib
import tarfile

from base64 import b64encode
from functools import partial
try:
    from itertools import zip_longest
except ImportError:
    from itertools import izip_longest as zip_longest

from multiprocessing.pool import ThreadPool

from google.protobuf import message

from django.apps import apps
from django.utils import translation
from django.contrib.auth.hashers import make_password
from django.core.serializers.json import DjangoJSONEncoder

from billiard.pool import Pool

from celery import shared_task, current_task
from celery.signals import worker_process_init, task_failure

from demos.apps.ea.tasks import crypto, pdf
from demos.apps.ea.tasks.masks import apply_mask
from demos.apps.ea.models import Election, Task, RemoteUser

from demos.common.utils import api, base32cf, config, dbsetup, enums
from demos.common.utils.permutation import permute


@shared_task(ignore_result=True)
def election_setup(election, election_obj, language):
	
	translation.activate(language)
	
	tag_bits = 1
	serial_bits = (election.ballots + 100).bit_length()
	credential_bits = config.CREDENTIAL_LEN * 8
	security_code_bits = config.SECURITY_CODE_LEN * 5
	token_bits = serial_bits + credential_bits + tag_bits + security_code_bits
	pad_bits = int(math.ceil(token_bits / 5.0) * 5 - token_bits)
	
	rand = random.SystemRandom()
	builder = pdf.BallotBuilder(election_obj)
	
	process_pool = Pool()
	thread_pool = ThreadPool(processes=4)
	
	app_config = apps.get_app_config('ea')
	
	# Update election state to WORKING
	
	election.state = enums.State.WORKING
	election.save(update_fields=['state'])
	
	election_obj['state'] = enums.State.WORKING
	
	# Establish sessions with the other servers
	
	api_session = {app_name: api.Session('ea', app_name, app_config)
		for app_name in ['abb', 'vbb', 'bds']}
	
	# Generate question keys and calculate max_options
	
	max_options = 0
	
	for question_obj in election_obj['__list_Question__']:
		
		options = len(question_obj['__list_OptionC__'])
		
		if options > max_options:
			max_options = options
			
		question_obj['key'] = crypto.gen_key(election.ballots, options)
	
	# Populate local and remote databases
	
	dbsetup.election(election, election_obj, app_config)
	
	data = {
		'task': 'election',
		'payload': election_obj,
	}
	
	api_setup1 = partial(api_setup, data=data,
		api_session=api_session, url_path='manage/setup/')
	
	thread_pool.map(api_setup1, ['abb', 'vbb', 'bds'])
	
	# Generate ballots in groups of BATCH_SIZE
	
	progress = {'current': 0, 'total': election.ballots * 2}
	current_task.update_state(state='PROGRESS', meta=progress)
	
	q_list = [(question_obj['key'], len(question_obj['__list_OptionC__'])) \
		for question_obj in election_obj['__list_Question__']]
	
	async_result = thread_pool.apply_async(crypto_gen, \
		(election.ballots, q_list, min(config.BATCH_SIZE, election.ballots)))
	
	for lo in range(100, election.ballots + 100, config.BATCH_SIZE):
		
		hi = lo + min(config.BATCH_SIZE, election.ballots + 100 - lo)
		
		# Get current batch's crypto elements and generate the next one's
		
		crypto_bsqo_list = async_result.get()
		
		if hi - 100 < election.ballots:
			async_result=thread_pool.apply_async(crypto_gen, (election.ballots,\
				q_list, min(config.BATCH_SIZE, election.ballots + 100 - hi)))
		
		# Generate the rest data for all ballots and parts and store them in
		# lists of dictionaries. They will be used to populate the databases.
		
		ballot_list = []
		
		for serial, crypto_sqo_list in zip(range(lo, hi), crypto_bsqo_list):
			
			# Generate a random credential and compute its hash value
			
			credential = os.urandom(config.CREDENTIAL_LEN)
			credential_int = int.from_bytes(credential, 'big')
			credential_hash = make_password(credential, hasher='_pbkdf2')
			
			ballot_obj = {
				'serial': serial,
				'credential': credential,
				'credential_hash': credential_hash,
				'__list_Part__': [],
			}
			
			for tag, crypto_qo_list in zip(['A', 'B'], crypto_sqo_list):
				
				# Generate a random security code and compute its hash value and
				# its hash's hash value. The client will use the first hash to
				# access the votecodes (as password) and to verify the security
				# code. The second hash uses the first hash's salt, reversed.
				
				security_code = base32cf.random(config.SECURITY_CODE_LEN)
				
				temp = make_password(security_code, hasher='_pbkdf2')
				salt, hash = temp.split('$')[2:]
				salt = salt[::-1]
				
				security_code_hash2 = make_password(hash,salt,hasher='_pbkdf2')
				
				part_obj = {
					'tag': tag,
					'security_code': security_code,
					'security_code_hash2': security_code_hash2,
					'__list_Question__': [],
				}
				
				for q_index, crypto_o_list in enumerate(crypto_qo_list):
					
					# Each ballot part's votecodes are grouped by question
					
					question_obj = {
						'__list_OptionV__': [],
					}
					
					# Generate short votecodes
					
					options = len(crypto_o_list)
					
					votecode_list = list(range(options))
					rand.shuffle(votecode_list)
					
					l_votecode_list = []
					
					if election.long_votecodes:
						
						# Long votecodes: each votecode is constructed as
						# follows: hmac(security_code, credential + (q_index *
						# max_options) + short_votecode), so that we get inique
						# votecodes across all questions. All votecode hashes
						# of a question in a ballot's part share the same salt.
						
						salt = None
						
						for votecode in votecode_list:
							
							key = base32cf.decode(security_code)
							bytes = math.ceil(key.bit_length() / 8.0)
							key = key.to_bytes(bytes, 'big')
							
							msg = credential_int+(q_index*max_options)+votecode
							bytes = math.ceil(msg.bit_length() / 8.0)
							msg = msg.to_bytes(bytes, 'big')
							
							hmac_obj = hmac.new(key, msg, digestmod='sha256')
							digest = int.from_bytes(hmac_obj.digest(), 'big')
							
							l_votecode = base32cf.\
								encode(digest)[-config.VOTECODE_LEN:]
							
							l_votecode_hash = make_password(l_votecode,
								salt=salt, hasher='_pbkdf2')
							
							if salt is None:
								salt = l_votecode_hash.split('$', 3)[2]
							
							l_votecode_list.append((l_votecode,l_votecode_hash))
					
					for votecode, l_votecode, crypto_list in zip_longest(\
						votecode_list, l_votecode_list, crypto_o_list):
						
						com, decom, zk1, zk_state = crypto_list
						l_votecode, l_votecode_hash = l_votecode or (None, None)
						
						# Generate receipt
						
						receipt = base32cf.random(config.RECEIPT_LEN)
						
						# 
						
						optionv_obj = {
							'votecode': votecode,
							'long_votecode': l_votecode,
							'long_votecode_hash': l_votecode_hash,
							'receipt': receipt,
							'com': com,
							'decom': decom,
							'zk1': zk1,
							'zk_state': zk_state,
						}
						
						question_obj['__list_OptionV__'].append(optionv_obj)
						
					part_obj['__list_Question__'].append(question_obj)
				
				ballot_obj['__list_Part__'].append(part_obj)
			
			# Build the vote tokens for both parts
			
			for i, part_obj in enumerate(ballot_obj['__list_Part__']):
				
				# Get the other part's security_code
				
				other_part_obj = ballot_obj['__list_Part__'][1-i]
				security_code = base32cf.decode(other_part_obj['security_code'])
				
				# The vote token consists of two parts. The first part is the
				# ballot's serial number and credential and the part's tag,
				# XORed with the second part. The second part is the other
				# part's security code, bit-inversed. This is done so that the
				# tokens of the two parts appear to be completely different.
				
				p1 = (serial << (tag_bits + credential_bits)) | \
					(int.from_bytes(credential, 'big') << tag_bits) | i
				
				p2 = (~security_code) & ((1 << security_code_bits) - 1)
				
				p1_len = serial_bits + credential_bits + tag_bits
				p2_len = security_code_bits
				
				for i in range(0, p1_len, p2_len):
					p1 ^= p2 << i
				
				p1 &= (1 << p1_len) - 1
				
				# Assemble the vote token and add random padding, if required
				
				p = (p1 << p2_len) | p2
				
				if pad_bits > 0:
					p |= (rand.getrandbits(pad_bits) << token_bits)
				
				# Encode the vote token
				
				vote_token = base32cf.encode(p)
				vote_token = vote_token.zfill((token_bits + pad_bits) // 5)
				
				part_obj['vote_token'] = vote_token
			
			ballot_list.append(ballot_obj)
			
			# Update progress status
			
			progress['current'] += 1
			current_task.update_state(state='PROGRESS', meta=progress)
		
		# Generate PDF ballots and keep them in an in-memory tar file
		
		tarbuf = io.BytesIO()
		tar = tarfile.open(fileobj=tarbuf, mode='w:gz')
		
		ballot_gen1 = partial(ballot_gen, builder=builder)
		pdf_list = process_pool.map(ballot_gen1, ballot_list)
		
		for serial, pdfbuf in pdf_list:
			
			tarinfo = tarfile.TarInfo()
			
			tarinfo.name = "%s.pdf" % serial
			tarinfo.size = len(pdfbuf.getvalue())
			tarinfo.mtime = time.time()
			
			pdfbuf.seek(0)
			tar.addfile(tarinfo=tarinfo, fileobj=pdfbuf)
			
			# Update progress status
			
			progress['current'] += 1
			current_task.update_state(state='PROGRESS', meta=progress)
		
		tar.close()
		
		# Get optionvs' permutations from the corresponding security codes
		
		for ballot_obj in ballot_list:
			
			for part_obj in ballot_obj['__list_Part__']:
				
				security_code = part_obj['security_code']
				
				for i, question_obj in enumerate(part_obj['__list_Question__']):
					
					optionv_list = question_obj['__list_OptionV__']
					
					# Get the n-th permutation of the optionv list, where
					# n is the hash of the current part's security code plus
					# the question's index, converted back to an integer.
					
					int_ = base32cf.decode(security_code) + i
					bytes_ = math.ceil(int_.bit_length() / 8.0)
					value = hashlib.sha256(int_.to_bytes(bytes_, 'big'))
					p_index = int.from_bytes(value.digest(), 'big')
					
					optionv_list = permute(optionv_list, p_index);
					
					# Set the indices in proper order
					
					for index, optionv in enumerate(optionv_list):
						optionv['index'] = index
					
					question_obj['__list_OptionV__'] = optionv_list
		
		# Populate local and remote databases
		
		election_obj_t = {
			'id': election_obj['id'],
			'__list_Ballot__': ballot_list,
		}
		
		dbsetup.ballot(election_obj_t, app_config)
		
		data = {
			'task': 'ballot',
			'payload': election_obj_t,
		}
		
		files = {
			'ballots.tar.gz': tarbuf.getvalue()
		}
		
		api_setup1 = partial(api_setup, data=data, files=files,
			api_session=api_session, url_path='manage/setup/')
		
		thread_pool.map(api_setup1, ['abb', 'vbb', 'bds'])
	
	# Update election state to RUNNING
	
	election.state = enums.State.RUNNING
	election.save(update_fields=['state'])
	
	data = {
		'model': 'Election',
		'natural_key': {
			'e_id': election_obj['id']
		},
		'fields': {
			'state': enums.State.RUNNING
		},
	}
	
	api_update1 = partial(api_update, data=data,
		api_session=api_session, url_path='manage/update/')
	
	thread_pool.map(api_update1, ['abb', 'vbb', 'bds'])
	
	# Delete celery task
	
	task = Task.objects.get(election_id=election.id)
	task.delete()
	
	translation.deactivate()


@task_failure.connect
def election_setup_failure_handler(*args, **kwargs):
	pass # TODO: database cleanup


def api_setup(app_name, **kwargs):
	
	# This function is used in a seperate thread.
	
	url_path = kwargs['url_path']
	api_session = kwargs['api_session']
	
	app_session = api_session[app_name]
	
	data = kwargs['data'].copy()
	files = kwargs.get('files')
	
	payload = apply_mask(app_name, data['payload'])
	data['payload'] = json.dumps(payload, \
		separators=(',', ':'), cls=CustomJSONEncoder)
	
	if app_name != 'bds':
		files = None
	
	app_session.post(url_path, data, files)


def api_update(app_name, **kwargs):
	
	# This function is used in a seperate thread.
	
	url_path = kwargs['url_path']
	api_session = kwargs['api_session']
	
	app_session = api_session[app_name]
	
	data = kwargs['data'].copy()
	json_data = json.dumps(data, separators=(',', ':'), cls=CustomJSONEncoder)
	
	data = { 'data': json_data }
	app_session.post(url_path, data)


def crypto_gen(ballots, q_list, number):
	
	# This function is used in a seperate thread.
	
	# Generates crypto elements and converts the returned list of questions of
	# ballots of parts of crypto elements to a list of ballots of parts of
	# questions of crypto elements!
	
	crypto_list = [crypto.gen_ballot(key, ballots, options, number) \
		for key, options in q_list]
	
	return zip(*[iter([j for i in zip(*crypto_list) for j in zip(*i)])] * 2)


def ballot_gen(ballot_obj, builder):
	
	# This function is used in a seperate process.
	
	serial = ballot_obj['serial']
	pdfbuf = builder.pdfgen(ballot_obj)
	
	return (serial, pdfbuf)


class CustomJSONEncoder(DjangoJSONEncoder):
	"""JSONEncoder subclass that supports date/time and protobuf types."""
	
	def default(self, o):
		
		if isinstance(o, message.Message):
			r = o.SerializeToString()
			r = b64encode(r).decode('ascii')
			return r
		
		return super(CustomJSONEncoder, self).default(o)

