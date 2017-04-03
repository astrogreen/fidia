# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings
import jsonfield.fields


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Query',
            fields=[
                ('id', models.AutoField(verbose_name='ID', auto_created=True, primary_key=True, serialize=False)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('updated', models.DateTimeField(auto_now=True)),
                ('title', models.CharField(max_length=100, blank=True, default='My Query')),
                ('SQL', models.TextField()),
                ('queryResults', jsonfield.fields.JSONField(default='')),
                ('flag', jsonfield.fields.JSONField(default='')),
                ('owner', models.ForeignKey(related_name='query', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ('created',),
            },
        ),
    ]
