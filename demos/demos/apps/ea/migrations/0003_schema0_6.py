# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ea', '0002_schema0_5'),
    ]

    operations = [
        migrations.AddField(
            model_name='election',
            name='parties_and_candidates',
            field=models.BooleanField(default=False),
        ),
    ]
