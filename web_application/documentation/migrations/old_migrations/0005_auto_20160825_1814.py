# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('documentation', '0004_auto_20160825_1320'),
    ]

    operations = [
        migrations.CreateModel(
            name='AAODC',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, primary_key=True, auto_created=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('updated', models.DateTimeField(auto_now=True)),
                ('title', models.CharField(max_length=100, default='Document Title')),
                ('content', models.TextField(max_length=100000, default='Content')),
                ('slug', models.SlugField(max_length=20, unique=True)),
            ],
        ),
        migrations.RenameModel(
            old_name='GAMADocumentation',
            new_name='GAMA',
        ),
        migrations.RenameModel(
            old_name='SAMIDocumentation',
            new_name='SAMI',
        ),
    ]
