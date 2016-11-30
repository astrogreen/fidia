# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import jsonfield.fields


class Migration(migrations.Migration):

    dependencies = [
        ('documentation', '0007_auto_20160826_1047'),
    ]

    operations = [
        migrations.AlterField(
            model_name='aaodc',
            name='route',
            field=jsonfield.fields.JSONField(max_length=100, default={}),
        ),
        migrations.AlterField(
            model_name='gama',
            name='route',
            field=jsonfield.fields.JSONField(max_length=100, default={}),
        ),
        migrations.AlterField(
            model_name='sami',
            name='route',
            field=jsonfield.fields.JSONField(max_length=100, default={}),
        ),
    ]
