# File: views.py

import json
import math
import logging
import requests
from six import string_types

from base64 import b64encode
try:
    from enum import IntEnum, unique
except ImportError:
    class IntEnum:
        pass
    def unique(fn):
        return fn

try:
    from urllib.parse import urljoin, quote
except ImportError:
    from urllib import quote
    from urlparse import urljoin

from django import http
from django.db import transaction
from django.apps import apps
from django.utils import timezone
from django.db.models import Count, Max
from django.shortcuts import render, redirect
from django.middleware import csrf
from django.views.generic import View
from django.core.exceptions import ValidationError
from django.utils.decorators import method_decorator
from django.core.urlresolvers import reverse
from django.contrib.auth.hashers import check_password, make_password

from demos.apps.vbb.models import Election, Question, Ballot, Part, \
    OptionV, OptionC

from demos.common.utils import api, base32cf, config, dbsetup, enums, hashers, intc
from demos.settings import DEMOS_URL

logger = logging.getLogger(__name__)
app_config = apps.get_app_config('vbb')


class HomeView(View):
    
    template_name = 'vbb/home.html'
    
    def get(self, request):
        return render(request, self.template_name, {})


class VoteView(View):
    
    template_name = 'vbb/vote.html'
    
    class Error(Exception):
        pass
    
    @unique
    class State(IntEnum):
        INVALID_ELECTION_ID = 1
        INVALID_VOTE_TOKEN = 2
        ELECTION_NOT_STARTED = 3
        ELECTION_PAUSED = 4
        ELECTION_ENDED = 5
        BALLOT_USED = 6
        SERVER_ERROR = 7
        REQUEST_ERROR = 8
        CONNECTION_ERROR = 9
        NO_ERROR = 0
    
    @staticmethod
    def _parse_input(election_id, vote_token,):
        
        retval = []
        
        # Get election from database
        
        try:
            election = Election.objects.get(id=election_id)
        except (ValidationError, Election.DoesNotExist):
            raise VoteView.Error(VoteView.State.INVALID_ELECTION_ID, *retval)
        
        retval.append(election)
        
        if election.state == enums.State.ERROR:
            raise VoteView.Error(VoteView.State.INVALID_ELECTION_ID, *retval)
        
        # Get question list from database
        
        try:
            question_qs = Question.objects.filter(election=election)
        except (ValidationError, Question.DoesNotExist):
            raise VoteView.Error(VoteView.State.SERVER_ERROR, *retval)
        
        retval.append(question_qs)
        
        # Verify election state
        
        now = timezone.now()
        
        if election.state == enums.State.WORKING or (election.state == \
            enums.State.RUNNING and now < election.start_datetime):
            raise VoteView.Error(VoteView.State.ELECTION_NOT_STARTED, *retval)
        
        elif election.state==enums.State.RUNNING and now>=election.end_datetime:
            raise VoteView.Error(VoteView.State.ELECTION_ENDED, *retval)
        
        elif election.state == enums.State.PAUSED:
            raise VoteView.Error(VoteView.State.ELECTION_PAUSED, *retval)
        
        elif election.state != enums.State.RUNNING:
            raise VoteView.Error(VoteView.State.SERVER_ERROR, *retval)
        
        # Vote token bits definitions
        
        tag_bits = 1
        serial_bits = (election.ballots + 100).bit_length()
        credential_bits = config.CREDENTIAL_LEN * 8
        security_code_bits = config.SECURITY_CODE_LEN * 5
        token_bits = serial_bits+credential_bits+tag_bits+security_code_bits
        
        # Verify vote token's length
        
        if not isinstance(vote_token, string_types):
            raise VoteView.Error(VoteView.State.INVALID_VOTE_TOKEN, *retval)
        
        if len(vote_token) != int(math.ceil(token_bits / 5.0)):
            raise VoteView.Error(VoteView.State.INVALID_VOTE_TOKEN, *retval)
        
        # The vote token consists of two parts. The first part is the
        # ballot's serial number and credential and the part's tag,
        # XORed with the second part. The second part is the other
        # part's security code, bit-inversed. This is done so that the
        # tokens of the two parts appear to be completely different.
        
        try:
            p = base32cf.decode(vote_token) & ((1 << token_bits) - 1)
        except (AttributeError, TypeError, ValueError):
            raise VoteView.Error(VoteView.State.INVALID_VOTE_TOKEN, *retval)
        
        p1_len = serial_bits + credential_bits + tag_bits
        p2_len = security_code_bits
        
        p1 = p >> p2_len
        p2 = p & ((1 << p2_len) - 1)
        
        for i in range(0, p1_len, p2_len):
            p1 ^= p2 << i
        
        p1 &= (1 << p1_len) - 1
        
        # Extract the selected part's serial number, credential and tag and
        # the other part's security code
        
        serial = (p1 >> credential_bits + tag_bits) & ((1 << serial_bits) - 1)
        
        credential = ((p1 >> tag_bits) & ((1 << credential_bits) - 1))
        credential = intc.to_bytes(credential, config.CREDENTIAL_LEN, 'big')
            
        tag = 'A' if p1 & ((1 << tag_bits) - 1) == 0 else 'B'
        
        security_code = base32cf.encode((~p2) & ((1 << security_code_bits) - 1))
        security_code = security_code.zfill(config.SECURITY_CODE_LEN)
        
        # Get ballot object and verify credential
        
        try:
            ballot = Ballot.objects.get(election=election, serial=serial)
        except (ValidationError, Ballot.DoesNotExist):
            raise VoteView.Error(VoteView.State.INVALID_VOTE_TOKEN, *retval)
        
        retval.append(ballot)
        
        if not check_password(credential, ballot.credential_hash):
            raise VoteView.Error(VoteView.State.INVALID_VOTE_TOKEN, *retval)
        
        # Get both part objects and verify the given security code. The first
        # matched object (part1) is always the part used by the client to vote,
        # the second matched object (part2) is the opposite part.
        
        order = ('' if tag == 'A' else '-') + 'tag'
        
        try:
            part_qs = Part.objects.filter(ballot=ballot).order_by(order)
        except (ValidationError, Part.DoesNotExist):
            raise VoteView.Error(VoteView.State.SERVER_ERROR, *retval)
        
        retval.append(part_qs)
        part2 = part_qs.last()
        
        salt = part2.security_code_hash2.split('$', 3)[2][::-1]
        password = make_password(security_code, salt, hasher='_pbkdf2')
        hash = password.split('$', 3)[3]
        
        retval.append(b64encode(credential).decode())
        
        if not check_password(hash, part2.security_code_hash2):
            raise VoteView.Error(VoteView.State.INVALID_VOTE_TOKEN, *retval)
        
        retval.append(security_code)
        
        # Check if the ballot is already used
        
        if ballot.used:
            raise VoteView.Error(VoteView.State.BALLOT_USED, *retval)
        
        retval.append(now)
        
        return retval
    
    def get(self, request, **kwargs):
        
        election_id = kwargs.get('election_id')
        vote_token = kwargs.get('vote_token')
        
        # Normalize election_id and vote_token
        
        args = {
            'election_id': election_id,
            'vote_token': vote_token,
        }
        
        normalized = False
        
        for key, value in args.items():
            
            try:
                args[key] = base32cf.normalize(value)
            except (AttributeError, TypeError, ValueError):
                pass
            else:
                normalized |= args[key] != value
        
        if normalized:
            return redirect('vbb:vote', **args)
        
        # Parse input 'election_id' and 'vote_token'. The first matched object
        # (part1) of part_qs is always the part used by the client to vote, the
        # second matched object (part2) is the other part. '_parse_input' method
        # raises a VoteView.Error exception for the first error that occurs.
        
        try:
            election, question_qs, ballot, (part1, _), credential, _, now = \
                VoteView._parse_input(election_id, vote_token)
        
        except VoteView.Error as e:
            
            status = 422
            args_len = len(e.args)
            now = timezone.now()
            
            context = {
                'state': e.args[0].value,
                'election': e.args[1] if args_len >= 2 else None,
                'questions': e.args[2] if args_len >= 3 else None,
                'serial': str(e.args[3].serial) if args_len >= 4 else None,
                'tag': e.args[4].first().tag if args_len >= 5 else None,
            }
        
        else:
            
            status = 200
            max_options = question_qs.\
                annotate(Count('optionc')).aggregate(Max('optionc__count'))
            abb_url = urljoin(DEMOS_URL['abb'], quote('%s/' % election_id))
            security_code_hash2_split = part1.security_code_hash2.split('$', 3)
            
            context = {
                'state': VoteView.State.NO_ERROR.value,
                'election': election,
                'questions': question_qs,
                'serial': str(ballot.serial),
                'tag': part1.tag,
                'abb_url': abb_url,
                'credential': credential,
                'votecode_len': config.VOTECODE_LEN,
                'max_options': max_options['optionc__count__max'],
                'sc_iterations': security_code_hash2_split[1],
                'sc_salt': security_code_hash2_split[2][::-1],
                'sc_length': config.SECURITY_CODE_LEN,
            }
        
        context.update({
            'timezone_now': now,
            'State': { s.name: s.value for s in VoteView.State },
        })
        
        csrf.get_token(request)
        return render(request, self.template_name, context, status=status)
    
    def post(self, request, **kwargs):
        
        election_id = kwargs.get('election_id')
        vote_token = kwargs.get('vote_token')
        
        # Parse input 'election_id' and 'vote_token'. The first matched object
        # (part1) of part_qs is always the part used by the client to vote, the
        # second matched object (part2) is the other part. '_parse_input' method
        # raises a VoteView.Error exception for the first error that occurs.
        
        try:
             election, question_qs, ballot, part_qs, credential, \
                security_code,_ = VoteView._parse_input(election_id, vote_token)
        except VoteView.Error as e:
            return http.JsonResponse({'error': e.args[0].value}, status=422)
        
        part1, part2 = part_qs
        error = { 'error': VoteView.State.REQUEST_ERROR }
        
        # Load POST's json field
        
        json_field = request.POST.get('jsonfield')
        
        try:
            json_obj = json.loads(json_field);
        except (TypeError, ValueError):
            return http.JsonResponse(error, status=422)
        
        # Perform the requested action
        
        if json_obj.get('command') == 'verify-security-code':
            
            # The client sends the security code's hash in order to verify.
            # Since this acts as the password, the server stores the hash's
            # hash, which uses the hash's salt, but reversed.
            
            hash = json_obj.get('hash')
            
            if not isinstance(hash, string_types):
                return http.JsonResponse(error, status=422)
            
            if not check_password(hash, part1.security_code_hash2):
                return http.HttpResponseForbidden()
            
            # Return a list of questions, where each question's element is a
            # list of (index, short_votecode) tuples. The client, who just
            # proved that knows the security code, is responsible for
            # restoring their correct order, using that security code.
            
            p1_votecodes = [
                (question.index, list(OptionV.objects.filter(part=part1,
                question=question).values_list('index', 'votecode')))
                for question in question_qs.iterator()
            ]
            
            return http.JsonResponse(p1_votecodes, safe=False)
        
        elif json_obj.get('command') == 'vote':
            
            vote_obj = json_obj.get('vote_obj')
            
            # Verify vote_obj's structure validity
            
            q_options = dict(question_qs.annotate(\
                Count('optionc')).values_list('index', 'optionc__count'))
            
            vc_type = int if not election.long_votecodes else str
            
            if not (isinstance(vote_obj, dict)
                and len(vote_obj) == len(q_options)
                and all(isinstance(q_index, string_types)
                and isinstance(vc_list, list)
                and 1 <= len(vc_list) <= q_options.get(int(q_index), -1)
                and all(isinstance(vc, vc_type) for vc in vc_list)
                    for q_index, vc_list in vote_obj.items())):
                
                return http.JsonResponse(error, status=422)
            
            # Verify votecodes, save vote and respond with the receipts
            
            response_obj = {}
            hasher = hashers.CustomPBKDF2PasswordHasher()
            
            try:
                for question in question_qs.iterator():
                    
                    optionv_qs = OptionV.objects.\
                        filter(part=part1, question=question)
                    
                    votecode_list = vote_obj[str(question.index)]
                    
                    if not election.long_votecodes:
                        
                        # Get only the requested short votecodes and receipts
                        
                        optionvs = dict(optionv_qs.filter(votecode__in=\
                            votecode_list).values_list('votecode', 'receipt'))
                        
                        # Return receipt list in the correct order
                        
                        receipt_list = [optionvs[vc] for vc in votecode_list]
                        
                    else:
                        
                        # Get all long votecode hashes and receipts
                        
                        optionvs = list(optionv_qs.\
                            values_list('l_votecode_hash', 'receipt'))
                        
                        vc_hashes, receipts = [list(o) for o in zip(*optionvs)]
                        
                        # Hash and compare all input votecodes with the ones in
                        # the list of hashes. Return the corresponding receipts.
                        
                        receipt_list = []
                        
                        for votecode in votecode_list:
                        
                            i = hasher.verify_list(votecode, vc_hashes)
                            if i == -1: break
                            
                            del vc_hashes[i]
                            receipt = receipts.pop(i)
                            
                            receipt_list.append(receipt)
                    
                    # If lengths do not match, at least one votecode was invalid
                    
                    if len(receipt_list) != len(votecode_list):
                        raise VoteView.Error(VoteView.State.REQUEST_ERROR)
                    
                    response_obj[str(question.index)] = receipt_list
                
                # Send vote data to the abb server
                
                abb_session = api.Session('vbb', 'abb', app_config)
                
                data = {
                    'votedata': json.dumps({
                        'e_id': election.id,
                        'b_serial': ballot.serial,
                        'b_credential': credential,
                        'p1_tag': part1.tag,
                        'p1_votecodes': vote_obj,
                        'p2_security_code': security_code,
                    })
                }
                
                abb_session.post('command/vote/', data)
                
                ballot.used = True
                ballot.save(update_fields=['used'])
            
            except requests.exceptions.RequestException:
                return http.JsonResponse(error, status=422)
            
            except VoteView.Error as e:
                return http.JsonResponse({'error': e.args[0].value}, status=422)
            
            except Exception:
                logger.exception('VoteView: Unexpected exception')
                return http.JsonResponse(error, status=422)
            
            else:
                return http.JsonResponse(response_obj, safe=False)
        
        return http.JsonResponse(error, status=422)


class QRCodeScannerView(View):
    
    template_name = 'vbb/qrcode.html'
    
    def get(self, request):
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

