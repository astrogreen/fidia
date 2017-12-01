# -*- coding: utf-8 -*-
# Generated by Django 1.9 on 2017-04-08 01:56
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('feature', '0003_auto_20170408_1139'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='feature',
            name='priority',
        ),
        migrations.AddField(
            model_name='feature',
            name='owner',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, related_name='feature', to=settings.AUTH_USER_MODEL),
        ),
    ]