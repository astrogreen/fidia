# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('restapi_app', '0006_auto_20160511_1611'),
    ]

    operations = [
        migrations.AlterField(
            model_name='query',
            name='row_flag',
            field=models.CharField(max_length=100),
        ),
    ]
