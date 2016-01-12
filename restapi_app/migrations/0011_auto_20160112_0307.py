# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('restapi_app', '0010_query'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='snippet',
            name='owner',
        ),
        migrations.DeleteModel(
            name='Snippet',
        ),
    ]
