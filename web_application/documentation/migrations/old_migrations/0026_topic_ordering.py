# -*- coding: utf-8 -*-
# Generated by Django 1.9 on 2016-09-01 01:28
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('documentation', '0025_article_image_caption'),
    ]

    operations = [
        migrations.AddField(
            model_name='topic',
            name='ordering',
            field=models.IntegerField(default='1'),
        ),
    ]
