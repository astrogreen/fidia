# -*- coding: utf-8 -*-
# Generated by Django 1.9 on 2016-10-29 01:43
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('documentation', '0036_remove_article_visitor_counter'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='article',
            name='image',
        ),
        migrations.RemoveField(
            model_name='article',
            name='image_caption',
        ),
    ]
