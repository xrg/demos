# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import demos.apps.bds.models
import demos.common.utils.fields
import demos.common.utils.storage
import demos.common.utils.enums


class Migration(migrations.Migration):

    dependencies = [
        ('bds', '0004_schema0_8'),
    ]

    operations = [
        migrations.AddField(
            model_name='election',
            name='ballots',
            field=models.PositiveIntegerField(default=2),
        ),
        migrations.AddField(
            model_name='election',
            name='type',
            field=demos.common.utils.fields.IntEnumField(default=2, cls=demos.common.utils.enums.Type, choices=[(b'ELECTIONS', 1), (b'REFERENDUM', 2)]),
        ),
        migrations.AddField(
            model_name='election',
            name='vc_type',
            field=demos.common.utils.fields.IntEnumField(default=1, cls=demos.common.utils.enums.VcType, choices=[(b'SHORT', 1), (b'LONG', 2)]),
        ),
    ]
