# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('documentation', '0011_auto_20160826_1147'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='topic',
            name='name',
        ),
    ]
