# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import jsonfield.fields


class Migration(migrations.Migration):

    dependencies = [
        ('restapi_app', '0002_auto_20160511_1557'),
    ]

    operations = [
        migrations.AlterField(
            model_name='query',
            name='flag',
            field=jsonfield.fields.JSONField(default=''),
        ),
    ]
