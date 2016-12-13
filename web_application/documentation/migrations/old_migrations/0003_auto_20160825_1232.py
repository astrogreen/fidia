# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('documentation', '0002_documentation_slug'),
    ]

    operations = [
        migrations.AlterField(
            model_name='documentation',
            name='slug',
            field=models.SlugField(unique=True, max_length=20),
        ),
    ]
