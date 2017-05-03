# -*- coding: utf-8 -*-
# Generated by Django 1.9 on 2017-05-03 03:36
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('query', '0034_auto_20170424_2236'),
    ]

    operations = [
        migrations.RenameField(
            model_name='query',
            old_name='hasError',
            new_name='has_error',
        ),
        migrations.RenameField(
            model_name='query',
            old_name='isCompleted',
            new_name='is_completed',
        ),
        migrations.RenameField(
            model_name='query',
            old_name='queryBuilderState',
            new_name='query_builder_state',
        ),
        migrations.RenameField(
            model_name='query',
            old_name='SQL',
            new_name='sql',
        ),
        migrations.RemoveField(
            model_name='query',
            name='results',
        ),
        migrations.AddField(
            model_name='query',
            name='row_count',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='query',
            name='table_name',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
    ]
