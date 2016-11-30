# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('documentation', '0024_auto_20160831_1140'),
    ]

    operations = [
        migrations.AddField(
            model_name='article',
            name='image_caption',
            field=models.CharField(null=True, blank=True, max_length=300),
        ),
    ]
