# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('restapi_app', '0013_auto_20160112_0917'),
    ]

    operations = [
        migrations.AlterField(
            model_name='version',
            name='survey',
            field=models.ForeignKey(related_name='version', to='restapi_app.Survey'),
        ),
    ]
