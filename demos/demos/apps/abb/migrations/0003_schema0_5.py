# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('abb', '0002_schema0_4'),
    ]

    operations = [
        migrations.AlterField(
            model_name='election',
            name='x509_cert',
            field=models.FileField(upload_to=b'get_upload_file_path'),
        ),
    ]
