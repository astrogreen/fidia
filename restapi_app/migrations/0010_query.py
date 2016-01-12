# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import jsonfield.fields
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('restapi_app', '0009_auto_20160111_0724'),
    ]

    operations = [
        migrations.CreateModel(
            name='Query',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True, auto_created=True, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('updated', models.DateTimeField(auto_now=True)),
                ('title', models.CharField(default='', blank=True, max_length=100)),
                ('SQL', models.TextField()),
                ('queryResults', jsonfield.fields.JSONField(default='')),
                ('owner', models.ForeignKey(to=settings.AUTH_USER_MODEL, related_name='query')),
            ],
            options={
                'ordering': ('created',),
            },
        ),
    ]
