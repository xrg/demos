# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('vbb', '0002_schema0_4'),
    ]

    operations = [
        migrations.AlterField(
            model_name='optionv',
            name='receipt',
            field=models.CharField(max_length=10),
        ),
    ]