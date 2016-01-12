# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('restapi_app', '0012_auto_20160112_0542'),
    ]

    operations = [
        migrations.AlterField(
            model_name='version',
            name='survey',
            field=models.ForeignKey(to='restapi_app.Survey'),
        ),
    ]
