# -*- coding: utf-8 -*-
# Generated by Django 1.9 on 2017-04-20 07:14
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('query', '0032_query_testfield'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='query',
            name='testField',
        ),
    ]
