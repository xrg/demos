# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import demos.common.utils.storage
import demos.common.utils.fields
import demos.apps.bds.models
import demos.common.utils.enums


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Ballot',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False, verbose_name='ID', auto_created=True)),
                ('serial', models.PositiveIntegerField()),
                ('pdf', models.FileField(storage=demos.common.utils.storage.TarFileStorage(), upload_to=demos.apps.bds.models.Ballot.get_upload_file_path)),
            ],
            options={
                'ordering': ['election', 'serial'],
            },
        ),
        migrations.CreateModel(
            name='Config',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False, verbose_name='ID', auto_created=True)),
                ('key', models.CharField(unique=True, max_length=128)),
                ('value', models.CharField(max_length=128)),
            ],
        ),
        migrations.CreateModel(
            name='Election',
            fields=[
                ('id', demos.common.utils.fields.Base32Field(primary_key=True, serialize=False)),
                ('title', models.CharField(max_length=128)),
                ('ballots', models.PositiveIntegerField()),
                ('start_datetime', models.DateTimeField()),
                ('end_datetime', models.DateTimeField()),
                ('state', demos.common.utils.fields.IntEnumField(cls=demos.common.utils.enums.State)),
            ],
            options={
                'ordering': ['id'],
            },
        ),
        migrations.CreateModel(
            name='Part',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False, verbose_name='ID', auto_created=True)),
                ('tag', models.CharField(choices=[('A', 'A'), ('B', 'B')], max_length=1)),
                ('vote_token', models.TextField()),
                ('security_code', models.CharField(max_length=8)),
                ('ballot', models.ForeignKey(to='bds.Ballot')),
            ],
            options={
                'ordering': ['ballot', 'tag'],
            },
        ),
        migrations.CreateModel(
            name='RemoteUser',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False, verbose_name='ID', auto_created=True)),
                ('username', models.CharField(unique=True, max_length=128)),
                ('password', models.CharField(max_length=128)),
            ],
        ),
        migrations.CreateModel(
            name='Task',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False, verbose_name='ID', auto_created=True)),
                ('task_id', models.UUIDField()),
                ('election_id', demos.common.utils.fields.Base32Field(unique=True)),
            ],
        ),
        migrations.CreateModel(
            name='Trustee',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False, verbose_name='ID', auto_created=True)),
                ('email', models.EmailField(max_length=254)),
                ('election', models.ForeignKey(to='bds.Election')),
            ],
        ),
        migrations.AddField(
            model_name='ballot',
            name='election',
            field=models.ForeignKey(to='bds.Election'),
        ),
        migrations.AlterUniqueTogether(
            name='trustee',
            unique_together=set([('election', 'email')]),
        ),
        migrations.AlterUniqueTogether(
            name='part',
            unique_together=set([('ballot', 'tag')]),
        ),
        migrations.AlterUniqueTogether(
            name='ballot',
            unique_together=set([('election', 'serial')]),
        ),
    ]
