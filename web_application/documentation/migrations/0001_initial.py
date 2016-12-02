# -*- coding: utf-8 -*-
# Generated by Django 1.9 on 2016-11-30 03:47
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion
import hitcount.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0007_alter_validators_add_error_messages'),
    ]

    operations = [
        migrations.CreateModel(
            name='Article',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(default='article title', max_length=200)),
                ('slug', models.SlugField(max_length=100)),
                ('content', models.TextField(default='Content', max_length=100000)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('updated', models.DateTimeField(auto_now=True)),
                ('hidden', models.BooleanField(default=False)),
                ('order', models.IntegerField(default=0)),
                ('edit_group', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='auth.Group')),
            ],
            bases=(models.Model, hitcount.models.HitCountMixin),
        ),
        migrations.CreateModel(
            name='Topic',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(default='topic title', max_length=200)),
                ('slug', models.SlugField(max_length=100, unique=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('updated', models.DateTimeField(auto_now=True)),
                ('ordering', models.IntegerField(unique=True)),
                ('hidden', models.BooleanField(default=False)),
            ],
        ),
        migrations.AddField(
            model_name='article',
            name='topic',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='articles', to='documentation.Topic'),
        ),
        migrations.AlterUniqueTogether(
            name='article',
            unique_together=set([('topic', 'slug')]),
        ),
    ]
