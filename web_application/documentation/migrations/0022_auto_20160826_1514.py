# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('documentation', '0021_auto_20160826_1456'),
    ]

    operations = [
        migrations.DeleteModel(
            name='AAODC',
        ),
        migrations.DeleteModel(
            name='GAMA',
        ),
        migrations.DeleteModel(
            name='SAMI',
        ),
    ]
