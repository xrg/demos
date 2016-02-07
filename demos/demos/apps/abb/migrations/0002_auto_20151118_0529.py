# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import demos.apps.abb.models
import demos.common.utils.storage


class Migration(migrations.Migration):

    dependencies = [
        ('abb', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='election',
            name='parties_and_candidates',
            field=models.BooleanField(default=False),
        ),
    ]
