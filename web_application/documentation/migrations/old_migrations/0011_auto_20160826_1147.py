# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('documentation', '0010_topics'),
    ]

    operations = [
        migrations.CreateModel(
            name='Article',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True, auto_created=True, verbose_name='ID')),
                ('title', models.CharField(default='article title', max_length=200)),
                ('article_slug', models.SlugField(default='article-slug', max_length=100)),
            ],
        ),
        migrations.CreateModel(
            name='Topic',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True, auto_created=True, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('title', models.CharField(default='topic title', max_length=200)),
                ('topic_slug', models.SlugField(unique=True, max_length=100)),
            ],
        ),
        migrations.DeleteModel(
            name='Topics',
        ),
        migrations.AddField(
            model_name='article',
            name='topic',
            field=models.ForeignKey(to='documentation.Topic', related_name='articles'),
        ),
        migrations.AlterUniqueTogether(
            name='article',
            unique_together=set([('topic', 'article_slug')]),
        ),
    ]
