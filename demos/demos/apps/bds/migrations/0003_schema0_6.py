# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import demos.apps.bds.models
import demos.common.utils.storage


class Migration(migrations.Migration):

    dependencies = [
        ('bds', '0002_schema0_5'),
    ]

    operations = [
        migrations.AddField(
            model_name='election',
            name='parties_and_candidates',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='ballot',
            name='pdf',
            field=models.FileField(storage=demos.common.utils.storage.PrivateTarFileStorage(tar_directory_permissions_mode=448, tar_file_permissions_mode=384, tar_permissions_mode=384, location=b'/home/panos/build/demos/data/bds/ballots'), upload_to=demos.apps.bds.models.get_ballot_file_path),
        ),
    ]
