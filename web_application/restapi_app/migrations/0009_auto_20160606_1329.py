# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('restapi_app', '0008_remove_query_row_flag'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='query',
            name='owner',
        ),
        migrations.DeleteModel(
            name='Query',
        ),
    ]
