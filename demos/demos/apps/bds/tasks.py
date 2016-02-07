# File: tasks.py

from __future__ import absolute_import, division, unicode_literals

import logging

from django.core import mail
from celery import shared_task

from demos.apps.bds.models import Election, Ballot, Task
from demos.common.utils.config import registry

logger = logging.getLogger(__name__)
config = registry.get_config('bds')


@shared_task
def send_email(election_id, email_list, serial_list):
    
    election = Election.objects.get(id=election_id)
    connection = mail.get_connection()
    
    for lo in range(100, len(serial_list) + 100, config.BATCH_SIZE):
        hi = lo + min(config.BATCH_SIZE, len(serial_list) + 100 - lo)
        
        messages = []
        
        ballot_qs = Ballot.objects.filter(election=election, \
            serial__in=serial_list)
        
        for email, ballot in zip(email_list, ballot_qs):
            
            pdfbuf = ballot.pdf.file
            
            subject = 'DemosVoting: Ballot for Election %s' % election.id
            body = 'Ballot: %s' % ballot.serial
            pdf = (pdfbuf.name, pdfbuf.read(), 'application/pdf')
            
            msg = mail.EmailMessage(subject=subject, body=body, 
                to=[email], attachments=[pdf])
            
            messages.append(msg)
        
        connection.send_messages(messages)
    
    # Delete celery task entry
    
    task = Task.objects.get(election=election)
    task.delete()

