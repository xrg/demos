# File: forms.py

from __future__ import absolute_import, division, unicode_literals

from django import forms
from django.utils.translation import ugettext_lazy as _

from demos.common.utils import fields
from demos.common.utils.config import registry

config = registry.get_config('ea')


class EmailForm(forms.Form):
    
    voter_list = fields.MultiEmailField(label=_('Voter e-mails'),
        min_length=1, max_length=config.MAX_TRUSTEES, required=False)
    
    csvfile = forms.FileField(label=_('E-mail csv file'), required=False)


class DownloadForm(forms.Form):
    
    ballots = forms.IntegerField(label=_('Ballots'),
        min_value=1, max_value=config.MAX_BALLOTS)
    
    archive_fmt = forms.ChoiceField(label=_('Archive format'), \
        choices=(('tar.gz', '.tar.gz'), ('zip', '.zip')),
        widget=forms.RadioSelect, initial='tar.gz')
