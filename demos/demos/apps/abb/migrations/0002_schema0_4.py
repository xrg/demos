# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('abb', '0001_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='optionv',
            old_name='long_votecode',
            new_name='l_votecode',
        ),
        migrations.RenameField(
            model_name='optionv',
            old_name='long_votecode_hash',
            new_name='l_votecode_hash',
        ),
        migrations.AddField(
            model_name='part',
            name='l_votecode_iterations',
            field=models.PositiveIntegerField(default=None, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='part',
            name='l_votecode_salt',
            field=models.CharField(default=b'', max_length=128, blank=True),
        ),
    ]
