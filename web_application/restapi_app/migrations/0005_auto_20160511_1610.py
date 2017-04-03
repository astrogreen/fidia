# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import jsonfield.fields


class Migration(migrations.Migration):

    dependencies = [
        ('restapi_app', '0004_auto_20160511_1609'),
    ]

    operations = [
        migrations.AlterField(
            model_name='query',
            name='row_flag',
            field=jsonfield.fields.JSONField(default="{'row_limit':100}"),
        ),
    ]
