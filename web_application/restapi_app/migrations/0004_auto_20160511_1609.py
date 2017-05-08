# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('restapi_app', '0003_auto_20160511_1559'),
    ]

    operations = [
        migrations.RenameField(
            model_name='query',
            old_name='flag',
            new_name='row_flag',
        ),
    ]
