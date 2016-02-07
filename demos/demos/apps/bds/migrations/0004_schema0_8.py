# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('bds', '0003_schema0_6'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='trustee',
            unique_together=set([]),
        ),
        migrations.RemoveField(
            model_name='trustee',
            name='election',
        ),
        migrations.RemoveField(
            model_name='election',
            name='parties_and_candidates',
        ),
        migrations.AddField(
            model_name='ballot',
            name='user',
            field=models.ForeignKey(default=None, blank=True, to=settings.AUTH_USER_MODEL, null=True),
        ),
        migrations.AddField(
            model_name='election',
            name='user',
            field=models.ForeignKey(related_name='+', default=1, to=settings.AUTH_USER_MODEL),
            preserve_default=False,
        ),
        migrations.DeleteModel(
            name='Trustee',
        ),
    ]
