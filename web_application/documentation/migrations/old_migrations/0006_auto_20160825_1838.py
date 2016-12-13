# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('documentation', '0005_auto_20160825_1814'),
    ]

    operations = [
        migrations.AlterField(
            model_name='aaodc',
            name='slug',
            field=models.SlugField(unique=True, max_length=100),
        ),
        migrations.AlterField(
            model_name='gama',
            name='slug',
            field=models.SlugField(unique=True, max_length=100),
        ),
        migrations.AlterField(
            model_name='sami',
            name='slug',
            field=models.SlugField(unique=True, max_length=100),
        ),
    ]
