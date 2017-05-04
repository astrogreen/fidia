# -*- coding: utf-8 -*-
# Generated by Django 1.9 on 2017-04-08 02:01
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('feature', '0004_auto_20170408_1156'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='feature',
            name='description',
        ),
        migrations.RemoveField(
            model_name='feature',
            name='name',
        ),
        migrations.RemoveField(
            model_name='feature',
            name='owner',
        ),
        migrations.RemoveField(
            model_name='feature',
            name='votes',
        ),
        migrations.AddField(
            model_name='feature',
            name='title',
            field=models.CharField(default='Title', max_length=140),
        ),
        migrations.AddField(
            model_name='feature',
            name='user',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='vote',
            name='user',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='vote',
            name='feature',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='votes', to='feature.Feature'),
        ),
        migrations.RemoveField(
            model_name='vote',
            name='owner',
        ),
        migrations.RemoveField(
            model_name='vote',
            name='upvote',
        ),
        migrations.AlterUniqueTogether(
            name='vote',
            unique_together=set([('feature', 'user')]),
        ),
    ]