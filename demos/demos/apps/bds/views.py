# File: views.py

from __future__ import division

import io
import csv
import time
import logging
import tarfile
import zipfile

from random import SystemRandom

from django import http
from django.db import transaction
from django.apps import apps
from django.utils import timezone
from django.shortcuts import render, redirect
from django.core.files import File
from django.views.generic import View
from django.core.serializers import deserialize
from django.core.exceptions import ValidationError
from django.utils.decorators import method_decorator
from django.core.urlresolvers import reverse

from demos.apps.bds.forms import DownloadForm, EmailForm
from demos.apps.bds.tasks import send_email
from demos.apps.bds.models import Election, Ballot, Task

from demos.common.utils import api, base32cf
from demos.common.utils.config import registry

logger = logging.getLogger(__name__)
app_config = apps.get_app_config('bds')
config = registry.get_config('bds')


class HomeView(View):

    template_name = 'bds/home.html'

    def get(self, request):
        return render(request, self.template_name, {})


class ManageView(View):

    template_name = 'bds/manage.html'

    def get(self, request, *args, **kwargs):

        election_id = kwargs.get('election_id')

        normalized = base32cf.normalize(election_id)
        if normalized != election_id:
            return redirect('bds:manage', election_id=normalized)

        try:
            election = Election.objects.get(id=election_id)
        except Election.DoesNotExist:
            election = None

        if not election:
            return redirect(reverse('ea:home') + '?error=id')


        available_ballots = Ballot.objects.\
            filter(election=election, user__isnull=True).count()

        context = {
            'election': election,
            'email_form': EmailForm(),
            'download_form': DownloadForm(),
            'available_ballots': str(available_ballots),
            'started': election.start_datetime <= timezone.now(),
        }

        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):

        election_id = kwargs.get('election_id')

        if election_id is None:
            return http.HttpResponseNotAllowed(['GET'])

        try:
            election = Election.objects.get(id=election_id)


        except (ValidationError, Election.DoesNotExist):
            return http.HttpResponse(status=422)

        download_form = DownloadForm(request.POST)
        email_form = EmailForm(request.POST, request.FILES)

        context = {
            'election': election,
            'email_form': email_form,
            'download_form': download_form,
            'started': election.start_datetime <= timezone.now(),
        }

        available_ballots = Ballot.objects.\
            filter(election=election, user__isnull=True).count()

        if download_form.is_valid():

            cleaned_data = download_form.cleaned_data

            ballots = int(cleaned_data['ballots'])
            archive_fmt = cleaned_data['archive_fmt']

            random = SystemRandom()

            with transaction.atomic():

                ballot_qs = Ballot.objects.select_for_update()

                available_serial_list = ballot_qs.filter(election=election, \
                    user=None).values_list('serial', flat=True)

                if len(available_serial_list) < ballots:
                    context['available_ballots'] = str(len(available_serial_list))
                    context['download_error'] = True
                    return render(request, self.template_name, context)

                serial_list = random.sample(available_serial_list, ballots)
                random.shuffle(serial_list)

                ballot_qs.filter(election=election,
                    serial__in=serial_list).update(user=request.user)

            ballot_qs = Ballot.objects.\
                filter(election=election, serial__in=serial_list)

            filebuf = io.BytesIO()

            if archive_fmt == 'tar.gz':

                extension = '.tar.gz'
                content_type = 'application/x-compressed-tar'

                with tarfile.open(fileobj=filebuf, mode='w:gz') as tar:

                    for ballot in ballot_qs:

                        tarinfo = tarfile.TarInfo()
                        pdfbuf = ballot.pdf.file

                        tarinfo.name = pdfbuf.name
                        tarinfo.size = pdfbuf.size
                        tarinfo.mtime = pdfbuf.mtime

                        tar.addfile(tarinfo=tarinfo, fileobj=pdfbuf.file)

            elif archive_fmt == 'zip':

                extension = '.zip'
                content_type = 'application/zip'

                with zipfile.ZipFile(file=filebuf, mode='w') as zip_:

                    for ballot in ballot_qs:

                        zipinfo = zipfile.ZipInfo()
                        pdfbuf = ballot.pdf.file

                        zipinfo.filename = pdfbuf.name
                        zipinfo.file_size = pdfbuf.size
                        zipinfo.date_time = time.gmtime(pdfbuf.mtime)[:6]

                        zip_.writestr(zipinfo, pdfbuf.read())

            response = http.FileResponse(filebuf.getvalue(), \
                content_type=content_type)

            response['Content-Disposition'] = 'attachment; filename=%s%s' % \
                (election_id, extension)

            return response

        elif email_form.is_valid():

            cleaned_data = email_form.cleaned_data
            voter_list = []

            if 'csvfile' in cleaned_data:

                csvfile = cleaned_data['csvfile']

                if hasattr(csvfile, 'temporary_file_path'):
                    csvfile = open(csvfile.temporary_file_path(), 'r')

                if csvfile:
                    csv_emails = [email[0] for email in list(csv.reader(csvfile))]

                    from django.core.validators import EmailValidator
                    from django.core.exceptions import ValidationError

                    validator = EmailValidator()

                    try:
                        for email in csv_emails:
                            validator(email)
                    except ValidationError:
                        context['available_ballots'] = str(available_ballots)
                        context['email_error'] = True
                        return render(request, self.template_name, context)

                    voter_list.extend(csv_emails)

            if 'voter_list' in cleaned_data:
                voter_list.extend(cleaned_data['voter_list'])

            random = SystemRandom()

            with transaction.atomic():

                ballot_qs = Ballot.objects.select_for_update()

                available_serial_list = ballot_qs.filter(election=election, \
                    user=None).values_list('serial', flat=True)

                if len(available_serial_list) < len(voter_list):
                    context['available_ballots'] = str(len(available_serial_list))
                    return render(request, self.template_name, context)

                serial_list = random.sample(available_serial_list, len(voter_list))
                random.shuffle(serial_list)

                ballot_qs.filter(election=election,
                    serial__in=serial_list).update(user=request.user)

            ballot_qs = Ballot.objects.\
                filter(election=election, serial__in=serial_list)

            task = send_email.s(election.id, voter_list, list(available_serial_list))
            task.freeze()

            Task.objects.create(election=election, task_id=task.id)
            task.apply_async()

            context['available_ballots'] = str(available_ballots)

            return render(request, self.template_name, context)

        return http.HttpResponseBadRequest()


# API Views --------------------------------------------------------------------

class ApiSetupView(api.ApiSetupView):

    def __init__(self, *args, **kwargs):
        kwargs['app_config'] = app_config
        super(ApiSetupView, self).__init__(*args, **kwargs)

    @method_decorator(api.user_required('ea'))
    def dispatch(self, *args, **kwargs):
        return super(ApiSetupView, self).dispatch(*args, **kwargs)

    def post(self, request, phase):

        try:
            election_obj = api.ApiSession.load_json_request(request.POST)

            if phase == 'p1':

                user = list(deserialize('json', election_obj['user']))[0]
                user.save()

                election_obj['user'] = user.object

            elif phase == 'p2':

                tarbuf = request.FILES['ballots.tar.gz']

                if hasattr(tarbuf, 'temporary_file_path'):
                    arg = {'name': tarbuf.temporary_file_path()}
                else:
                    arg = {'fileobj': tarbuf}

                tar = tarfile.open(mode='r:*', **arg)

                for ballot_obj in election_obj['__list_Ballot__']:

                    pdfname = "%s.pdf" % ballot_obj['serial']

                    tarinfo = tar.getmember(pdfname)
                    pdfbuf = tar.extractfile(tarinfo)

                    ballot_obj['pdf'] = File(pdfbuf, name=pdfname)

        except Exception:
            logger.exception('SetupView: API error')
            return http.HttpResponse(status=422)

        return super(ApiSetupView, self).post(request, election_obj)


class ApiUpdateView(api.ApiUpdateView):

    def __init__(self, *args, **kwargs):
        kwargs['app_config'] = app_config
        super(ApiUpdateView, self).__init__(*args, **kwargs)

    @method_decorator(api.user_required('ea'))
    def dispatch(self, *args, **kwargs):
        return super(ApiUpdateView, self).dispatch(*args, **kwargs)

#eof
