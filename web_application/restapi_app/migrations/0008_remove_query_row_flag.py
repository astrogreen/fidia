# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('restapi_app', '0007_auto_20160511_1620'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='query',
            name='row_flag',
        ),
    ]
