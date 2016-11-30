# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('documentation', '0008_auto_20160826_1118'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='aaodc',
            name='route',
        ),
        migrations.RemoveField(
            model_name='gama',
            name='route',
        ),
        migrations.RemoveField(
            model_name='sami',
            name='route',
        ),
        migrations.AddField(
            model_name='aaodc',
            name='route_name',
            field=models.CharField(default='', max_length=100),
        ),
        migrations.AddField(
            model_name='gama',
            name='route_name',
            field=models.CharField(default='', max_length=100),
        ),
        migrations.AddField(
            model_name='sami',
            name='route_name',
            field=models.CharField(default='documentation:sami-docs-detail', max_length=100),
        ),
    ]
