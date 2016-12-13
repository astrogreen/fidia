# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('documentation', '0003_auto_20160825_1232'),
    ]

    operations = [
        migrations.CreateModel(
            name='GAMADocumentation',
            fields=[
                ('id', models.AutoField(auto_created=True, serialize=False, verbose_name='ID', primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('updated', models.DateTimeField(auto_now=True)),
                ('title', models.CharField(max_length=100, default='Document Title')),
                ('content', models.TextField(max_length=100000, default='Content')),
                ('slug', models.SlugField(max_length=20, unique=True)),
            ],
        ),
        migrations.RenameModel(
            old_name='Documentation',
            new_name='SAMIDocumentation',
        ),
    ]
