# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import demos.common.utils.crypto.crypto_pb2
import demos.common.utils.fields
import demos.common.utils.enums


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Ballot',
            fields=[
                ('id', models.AutoField(verbose_name='ID', auto_created=True, serialize=False, primary_key=True)),
                ('serial', models.PositiveIntegerField()),
            ],
            options={
                'ordering': ['election', 'serial'],
            },
        ),
        migrations.CreateModel(
            name='Config',
            fields=[
                ('id', models.AutoField(verbose_name='ID', auto_created=True, serialize=False, primary_key=True)),
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
            name='OptionC',
            fields=[
                ('id', models.AutoField(verbose_name='ID', auto_created=True, serialize=False, primary_key=True)),
                ('text', models.CharField(max_length=128)),
                ('index', models.PositiveSmallIntegerField()),
            ],
            options={
                'ordering': ['question', 'index'],
            },
        ),
        migrations.CreateModel(
            name='OptionV',
            fields=[
                ('id', models.AutoField(verbose_name='ID', auto_created=True, serialize=False, primary_key=True)),
                ('votecode', models.CharField(max_length=6)),
                ('com', demos.common.utils.fields.ProtoField(cls=demos.common.utils.crypto.crypto_pb2.Com)),
                ('zk1', demos.common.utils.fields.ProtoField(cls=demos.common.utils.crypto.crypto_pb2.ZK1)),
                ('zk2', demos.common.utils.fields.ProtoField(cls=demos.common.utils.crypto.crypto_pb2.ZK2, blank=True, null=True, default=None)),
                ('voted', models.BooleanField(default=False)),
                ('index', models.PositiveSmallIntegerField()),
            ],
            options={
                'ordering': ['part', 'question', 'index'],
            },
        ),
        migrations.CreateModel(
            name='Part',
            fields=[
                ('id', models.AutoField(verbose_name='ID', auto_created=True, serialize=False, primary_key=True)),
                ('tag', models.CharField(choices=[('A', 'A'), ('B', 'B')], max_length=1)),
                ('security_code', models.CharField(blank=True, max_length=8, default='')),
                ('ballot', models.ForeignKey(to='abb.Ballot')),
            ],
            options={
                'ordering': ['ballot', 'tag'],
            },
        ),
        migrations.CreateModel(
            name='Question',
            fields=[
                ('id', models.AutoField(verbose_name='ID', auto_created=True, serialize=False, primary_key=True)),
                ('text', models.CharField(max_length=128)),
                ('index', models.PositiveSmallIntegerField()),
                ('choices', models.PositiveSmallIntegerField()),
                ('key', demos.common.utils.fields.ProtoField(cls=demos.common.utils.crypto.crypto_pb2.Key)),
                ('added_com', demos.common.utils.fields.ProtoField(cls=demos.common.utils.crypto.crypto_pb2.Com, blank=True, null=True, default=None)),
                ('added_decom', demos.common.utils.fields.ProtoField(cls=demos.common.utils.crypto.crypto_pb2.Decom, blank=True, null=True, default=None)),
                ('coins', models.CharField(blank=True, max_length=128, default='')),
                ('election', models.ForeignKey(to='abb.Election')),
                ('m2m_parts', models.ManyToManyField(to='abb.Part')),
            ],
            options={
                'ordering': ['election', 'index'],
            },
        ),
        migrations.CreateModel(
            name='RemoteUser',
            fields=[
                ('id', models.AutoField(verbose_name='ID', auto_created=True, serialize=False, primary_key=True)),
                ('username', models.CharField(unique=True, max_length=128)),
                ('password', models.CharField(max_length=128)),
            ],
        ),
        migrations.CreateModel(
            name='Task',
            fields=[
                ('id', models.AutoField(verbose_name='ID', auto_created=True, serialize=False, primary_key=True)),
                ('task_id', models.UUIDField()),
                ('election_id', demos.common.utils.fields.Base32Field(unique=True)),
            ],
        ),
        migrations.AddField(
            model_name='optionv',
            name='part',
            field=models.ForeignKey(to='abb.Part'),
        ),
        migrations.AddField(
            model_name='optionv',
            name='question',
            field=models.ForeignKey(to='abb.Question'),
        ),
        migrations.AddField(
            model_name='optionc',
            name='question',
            field=models.ForeignKey(to='abb.Question'),
        ),
        migrations.AddField(
            model_name='ballot',
            name='election',
            field=models.ForeignKey(to='abb.Election'),
        ),
        migrations.AlterUniqueTogether(
            name='question',
            unique_together=set([('election', 'index')]),
        ),
        migrations.AlterUniqueTogether(
            name='part',
            unique_together=set([('ballot', 'tag')]),
        ),
        migrations.AlterUniqueTogether(
            name='optionv',
            unique_together=set([('part', 'question', 'votecode')]),
        ),
        migrations.AlterUniqueTogether(
            name='optionc',
            unique_together=set([('question', 'text')]),
        ),
        migrations.AlterUniqueTogether(
            name='ballot',
            unique_together=set([('election', 'serial')]),
        ),
    ]
