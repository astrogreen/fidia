# -*- coding: utf-8 -*-
# Generated by Django 1.9 on 2017-02-22 03:11
from __future__ import unicode_literals

from django.db import migrations
import jsonfield.fields


class Migration(migrations.Migration):

    dependencies = [
        ('query', '0002_auto_20160606_1329'),
    ]

    operations = [
        migrations.AddField(
            model_name='query',
            name='queryBuilderState',
            field=jsonfield.fields.JSONField(default=''),
        ),
    ]