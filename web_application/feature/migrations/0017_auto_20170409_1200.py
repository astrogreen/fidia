# -*- coding: utf-8 -*-
# Generated by Django 1.9 on 2017-04-09 02:00
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('feature', '0016_auto_20170409_1200'),
    ]

    operations = [
        migrations.AddField(
            model_name='feature',
            name='num_vote_down',
            field=models.PositiveIntegerField(db_index=True, default=0),
        ),
        migrations.AddField(
            model_name='feature',
            name='num_vote_up',
            field=models.PositiveIntegerField(db_index=True, default=0),
        ),
        migrations.AddField(
            model_name='feature',
            name='vote_score',
            field=models.IntegerField(db_index=True, default=0),
        ),
    ]