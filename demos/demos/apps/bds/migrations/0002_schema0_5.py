# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import demos.common.utils.storage


class Migration(migrations.Migration):

    dependencies = [
        ('bds', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='ballot',
            name='pdf',
            field=models.FileField(storage=demos.common.utils.storage.TarFileStorage(), upload_to=b'get_upload_file_path'),
        ),
    ]
