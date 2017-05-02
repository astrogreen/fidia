# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('restapi_app', '0005_auto_20160511_1610'),
    ]

    operations = [
        migrations.AlterField(
            model_name='query',
            name='row_flag',
            field=models.CharField(default='test_flag', blank=True, max_length=100),
        ),
    ]
