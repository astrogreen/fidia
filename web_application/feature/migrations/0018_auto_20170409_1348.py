# -*- coding: utf-8 -*-
# Generated by Django 1.9 on 2017-04-09 03:48
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('feature', '0017_auto_20170409_1200'),
    ]

    operations = [
        migrations.CreateModel(
            name='Vote',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('vote_score', models.IntegerField(db_index=True, default=0)),
                ('num_vote_up', models.PositiveIntegerField(db_index=True, default=0)),
                ('num_vote_down', models.PositiveIntegerField(db_index=True, default=0)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.RemoveField(
            model_name='feature',
            name='num_vote_down',
        ),
        migrations.RemoveField(
            model_name='feature',
            name='num_vote_up',
        ),
        migrations.RemoveField(
            model_name='feature',
            name='vote_score',
        ),
        migrations.AddField(
            model_name='vote',
            name='feature',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='feature_votes', to='feature.Feature'),
        ),
    ]