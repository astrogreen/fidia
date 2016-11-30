# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('documentation', '0013_auto_20160826_1226'),
    ]

    operations = [
        migrations.AddField(
            model_name='article',
            name='slug',
            field=models.SlugField(default='slug1', max_length=100, unique=True),
        ),
        migrations.AlterUniqueTogether(
            name='article',
            unique_together=set([('topic', 'slug')]),
        ),
        migrations.RemoveField(
            model_name='article',
            name='article_slug',
        ),
    ]
