# -*- coding: utf-8 -*-
# Generated by Django 1.9 on 2017-04-11 23:58
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('feature', '0030_auto_20170411_1525'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='vote',
            name='num_vote_down',
        ),
        migrations.RemoveField(
            model_name='vote',
            name='num_vote_up',
        ),
        migrations.RemoveField(
            model_name='vote',
            name='vote_score',
        ),
    ]
