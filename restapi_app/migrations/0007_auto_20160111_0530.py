# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('restapi_app', '0006_survey'),
    ]

    operations = [
        migrations.DeleteModel(
            name='Products',
        ),
        migrations.DeleteModel(
            name='Version',
        ),
    ]
