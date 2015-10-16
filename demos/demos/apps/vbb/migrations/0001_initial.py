# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import demos.common.utils.fields
import demos.common.utils.enums


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Ballot',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='ID', auto_created=True, serialize=False)),
                ('serial', models.PositiveIntegerField()),
                ('credential_hash', models.CharField(max_length=128)),
            ],
            options={
                'ordering': ['election', 'serial'],
            },
        ),
        migrations.CreateModel(
            name='Config',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='ID', auto_created=True, serialize=False)),
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
                ('id', models.AutoField(primary_key=True, verbose_name='ID', auto_created=True, serialize=False)),
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
                ('id', models.AutoField(primary_key=True, verbose_name='ID', auto_created=True, serialize=False)),
                ('votecode', models.CharField(max_length=6)),
                ('receipt', models.CharField(max_length=6)),
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
                ('id', models.AutoField(primary_key=True, verbose_name='ID', auto_created=True, serialize=False)),
                ('tag', models.CharField(choices=[('A', 'A'), ('B', 'B')], max_length=1)),
                ('security_code_hash', models.CharField(max_length=128)),
                ('security_code', models.CharField(default='', max_length=8, blank=True)),
                ('ballot', models.ForeignKey(to='vbb.Ballot')),
            ],
            options={
                'ordering': ['ballot', 'tag'],
            },
        ),
        migrations.CreateModel(
            name='Question',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='ID', auto_created=True, serialize=False)),
                ('text', models.CharField(max_length=128)),
                ('index', models.PositiveSmallIntegerField()),
                ('columns', models.PositiveSmallIntegerField()),
                ('choices', models.PositiveSmallIntegerField()),
                ('election', models.ForeignKey(to='vbb.Election')),
                ('m2m_parts', models.ManyToManyField(to='vbb.Part')),
            ],
            options={
                'ordering': ['election', 'index'],
            },
        ),
        migrations.CreateModel(
            name='RemoteUser',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='ID', auto_created=True, serialize=False)),
                ('username', models.CharField(unique=True, max_length=128)),
                ('password', models.CharField(max_length=128)),
            ],
        ),
        migrations.CreateModel(
            name='Task',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='ID', auto_created=True, serialize=False)),
                ('task_id', models.UUIDField()),
                ('election_id', demos.common.utils.fields.Base32Field(unique=True)),
            ],
        ),
        migrations.AddField(
            model_name='optionv',
            name='part',
            field=models.ForeignKey(to='vbb.Part'),
        ),
        migrations.AddField(
            model_name='optionv',
            name='question',
            field=models.ForeignKey(to='vbb.Question'),
        ),
        migrations.AddField(
            model_name='optionc',
            name='question',
            field=models.ForeignKey(to='vbb.Question'),
        ),
        migrations.AddField(
            model_name='ballot',
            name='election',
            field=models.ForeignKey(to='vbb.Election'),
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
