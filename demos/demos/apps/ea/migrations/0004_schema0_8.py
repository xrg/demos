# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('ea', '0003_schema0_6'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='election',
            name='parties_and_candidates',
        ),
        migrations.AddField(
            model_name='election',
            name='user',
            field=models.ForeignKey(default=1, to=settings.AUTH_USER_MODEL),
            preserve_default=False,
        ),
    ]
