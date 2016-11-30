# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import datetime
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        ('documentation', '0019_auto_20160826_1344'),
    ]

    operations = [
        migrations.AddField(
            model_name='article',
            name='created',
            field=models.DateTimeField(auto_now_add=True, default=datetime.datetime(2016, 8, 26, 3, 55, 20, 178814, tzinfo=utc)),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='article',
            name='updated',
            field=models.DateTimeField(auto_now=True, default=datetime.datetime(2016, 8, 26, 3, 55, 27, 715213, tzinfo=utc)),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='topic',
            name='created',
            field=models.DateTimeField(auto_now_add=True, default=datetime.datetime(2016, 8, 26, 3, 55, 43, 859960, tzinfo=utc)),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='topic',
            name='updated',
            field=models.DateTimeField(auto_now=True, default=datetime.datetime(2016, 8, 26, 3, 55, 48, 547931, tzinfo=utc)),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='topic',
            name='slug',
            field=models.SlugField(unique=True, max_length=100),
        ),
    ]
