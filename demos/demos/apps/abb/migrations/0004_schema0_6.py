# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import demos.apps.abb.models
import demos.common.utils.storage


class Migration(migrations.Migration):

    dependencies = [
        ('abb', '0003_schema0_5'),
    ]

    operations = [
        migrations.AddField(
            model_name='election',
            name='parties_and_candidates',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='election',
            name='cert',
            field=models.FileField(storage=demos.common.utils.storage.PrivateFileSystemStorage(file_permissions_mode=384, directory_permissions_mode=448, location=b'/home/panos/build/demos/data/abb'), upload_to=demos.apps.abb.models.get_cert_file_path),
        ),
        migrations.AlterField(
            model_name='election',
            name='export_file',
            field=models.FileField(storage=demos.common.utils.storage.PrivateFileSystemStorage(file_permissions_mode=384, directory_permissions_mode=448, location=b'/home/panos/build/demos/data/abb'), upload_to=demos.apps.abb.models.get_export_file_path, blank=True),
        ),
    ]
