# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import demos.common.utils.crypto.crypto_pb2
import demos.common.utils.enums
import demos.common.utils.fields


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Ballot',
            fields=[
                ('id', models.AutoField(auto_created=True, serialize=False, verbose_name='ID', primary_key=True)),
                ('serial', models.PositiveIntegerField()),
            ],
            options={
                'ordering': ['election', 'serial'],
            },
        ),
        migrations.CreateModel(
            name='Config',
            fields=[
                ('id', models.AutoField(auto_created=True, serialize=False, verbose_name='ID', primary_key=True)),
                ('key', models.CharField(max_length=128, unique=True)),
                ('value', models.CharField(max_length=128, blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='Election',
            fields=[
                ('id', demos.common.utils.fields.Base32Field(serialize=False, primary_key=True)),
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
                ('id', models.AutoField(auto_created=True, serialize=False, verbose_name='ID', primary_key=True)),
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
                ('id', models.AutoField(auto_created=True, serialize=False, verbose_name='ID', primary_key=True)),
                ('votecode', models.CharField(max_length=6)),
                ('com', demos.common.utils.fields.ProtoField(cls=demos.common.utils.crypto.crypto_pb2.Com)),
                ('decom', demos.common.utils.fields.ProtoField(cls=demos.common.utils.crypto.crypto_pb2.Decom)),
                ('zk1', demos.common.utils.fields.ProtoField(cls=demos.common.utils.crypto.crypto_pb2.ZK1)),
                ('zk_state', demos.common.utils.fields.ProtoField(cls=demos.common.utils.crypto.crypto_pb2.ZKState)),
                ('zk2', demos.common.utils.fields.ProtoField(blank=True, default=None, cls=demos.common.utils.crypto.crypto_pb2.ZK2, null=True)),
                ('index', models.PositiveSmallIntegerField()),
            ],
            options={
                'ordering': ['part', 'question', 'index'],
            },
        ),
        migrations.CreateModel(
            name='Part',
            fields=[
                ('id', models.AutoField(auto_created=True, serialize=False, verbose_name='ID', primary_key=True)),
                ('tag', models.CharField(max_length=1, choices=[('A', 'A'), ('B', 'B')])),
                ('ballot', models.ForeignKey(to='ea.Ballot')),
            ],
            options={
                'ordering': ['ballot', 'tag'],
            },
        ),
        migrations.CreateModel(
            name='Question',
            fields=[
                ('id', models.AutoField(auto_created=True, serialize=False, verbose_name='ID', primary_key=True)),
                ('text', models.CharField(max_length=128)),
                ('index', models.PositiveSmallIntegerField()),
                ('key', demos.common.utils.fields.ProtoField(cls=demos.common.utils.crypto.crypto_pb2.Key)),
                ('election', models.ForeignKey(to='ea.Election')),
                ('m2m_parts', models.ManyToManyField(to='ea.Part')),
            ],
            options={
                'ordering': ['election', 'index'],
            },
        ),
        migrations.CreateModel(
            name='RemoteUser',
            fields=[
                ('id', models.AutoField(auto_created=True, serialize=False, verbose_name='ID', primary_key=True)),
                ('username', models.CharField(max_length=128, unique=True)),
                ('password', models.CharField(max_length=128)),
            ],
        ),
        migrations.CreateModel(
            name='Task',
            fields=[
                ('id', models.AutoField(auto_created=True, serialize=False, verbose_name='ID', primary_key=True)),
                ('task_id', models.UUIDField()),
                ('election_id', demos.common.utils.fields.Base32Field(unique=True)),
            ],
        ),
        migrations.CreateModel(
            name='Trustee',
            fields=[
                ('id', models.AutoField(auto_created=True, serialize=False, verbose_name='ID', primary_key=True)),
                ('email', models.EmailField(max_length=254)),
                ('election', models.ForeignKey(to='ea.Election')),
            ],
        ),
        migrations.AddField(
            model_name='optionv',
            name='part',
            field=models.ForeignKey(to='ea.Part'),
        ),
        migrations.AddField(
            model_name='optionv',
            name='question',
            field=models.ForeignKey(to='ea.Question'),
        ),
        migrations.AddField(
            model_name='optionc',
            name='question',
            field=models.ForeignKey(to='ea.Question'),
        ),
        migrations.AddField(
            model_name='ballot',
            name='election',
            field=models.ForeignKey(to='ea.Election'),
        ),
        migrations.AlterUniqueTogether(
            name='trustee',
            unique_together=set([('election', 'email')]),
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
