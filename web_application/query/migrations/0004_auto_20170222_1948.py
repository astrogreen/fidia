# -*- coding: utf-8 -*-
# Generated by Django 1.9 on 2017-02-22 08:48
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('query', '0003_query_querybuilderstate'),
    ]

    operations = [
        migrations.AlterField(
            model_name='query',
            name='queryBuilderState',
            field=models.TextField(),
        ),
        migrations.AlterField(
            model_name='query',
            name='queryResults',
            field=models.TextField(null=True),
        ),
    ]
