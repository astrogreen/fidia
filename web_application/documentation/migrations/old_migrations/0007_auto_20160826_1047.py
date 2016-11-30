# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import jsonfield.fields


class Migration(migrations.Migration):

    dependencies = [
        ('documentation', '0006_auto_20160825_1838'),
    ]

    operations = [
        migrations.AddField(
            model_name='aaodc',
            name='route',
            field=jsonfield.fields.JSONField(max_length=100, default='{}'),
        ),
        migrations.AddField(
            model_name='gama',
            name='route',
            field=jsonfield.fields.JSONField(max_length=100, default='{}'),
        ),
        migrations.AddField(
            model_name='sami',
            name='route',
            field=jsonfield.fields.JSONField(max_length=100, default='{}'),
        ),
    ]
