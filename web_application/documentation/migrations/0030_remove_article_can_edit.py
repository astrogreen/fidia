# -*- coding: utf-8 -*-
# Generated by Django 1.9 on 2016-09-05 09:30
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('documentation', '0029_article_can_edit'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='article',
            name='can_edit',
        ),
    ]
