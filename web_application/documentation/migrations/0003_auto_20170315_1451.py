# -*- coding: utf-8 -*-
# Generated by Django 1.9 on 2017-03-15 03:51
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('documentation', '0002_auto_20161130_1701'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='article',
            name='hidden',
        ),
        migrations.RemoveField(
            model_name='topic',
            name='hidden',
        ),
    ]