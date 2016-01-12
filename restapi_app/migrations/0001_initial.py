# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import jsonfield.fields
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Snippet',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('updated', models.DateTimeField(auto_now=True)),
                ('title', models.CharField(default='', max_length=100, blank=True)),
                ('SQL', models.TextField()),
                ('queryResults', jsonfield.fields.JSONField(default='')),
                ('owner', models.ForeignKey(to=settings.AUTH_USER_MODEL, related_name='snippets')),
            ],
            options={
                'ordering': ('created',),
            },
        ),
    ]
