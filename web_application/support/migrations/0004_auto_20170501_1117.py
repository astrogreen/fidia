# -*- coding: utf-8 -*-
# Generated by Django 1.9 on 2017-05-01 01:17
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('support', '0003_auto_20170501_1116'),
    ]

    operations = [
        migrations.AlterField(
            model_name='bugreport',
            name='url',
            field=models.CharField(blank=True, max_length=100),
        ),
    ]
