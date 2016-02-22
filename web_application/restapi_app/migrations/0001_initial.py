# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import jsonfield.fields
import restapi_app.models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='AstroObject',
            fields=[
                ('id', models.AutoField(verbose_name='ID', auto_created=True, primary_key=True, serialize=False)),
                ('type', models.CharField(max_length=100, choices=[('galaxy', 'galaxy'), ('star', 'star'), ('group', 'group')])),
                ('ASVOID', models.IntegerField(default=restapi_app.models.AstroObject.number, unique=True)),
            ],
        ),
        migrations.CreateModel(
            name='Catalogue',
            fields=[
                ('id', models.AutoField(verbose_name='ID', auto_created=True, primary_key=True, serialize=False)),
                ('title', models.CharField(max_length=100)),
                ('content', jsonfield.fields.JSONField(default='table of content')),
                ('meta', jsonfield.fields.JSONField(default='metadata')),
                ('version', models.DecimalField(decimal_places=2, max_digits=4)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('updated', models.DateTimeField(auto_now=True)),
                ('slugField', models.SlugField(max_length=200, unique=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='CatalogueGroup',
            fields=[
                ('id', models.AutoField(verbose_name='ID', auto_created=True, primary_key=True, serialize=False)),
                ('group', models.CharField(max_length=100, unique=True, choices=[('GroupFinding', 'GroupFinding'), ('InputCat', 'InputCat')])),
                ('slugField', models.SlugField(max_length=200, unique=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='GAMAPublic',
            fields=[
                ('id', models.AutoField(verbose_name='ID', auto_created=True, primary_key=True, serialize=False)),
                ('ASVOID', models.CharField(max_length=100)),
                ('InputCatA', jsonfield.fields.JSONField(blank=True, default='')),
                ('TilingCat', jsonfield.fields.JSONField(blank=True, default='')),
                ('SpecAll', jsonfield.fields.JSONField(blank=True, default='')),
                ('SersicCat', jsonfield.fields.JSONField(blank=True, default='')),
                ('Spectrum', models.ImageField(blank=True, upload_to='uploads/%Y/%m/%d/', null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Image',
            fields=[
                ('id', models.AutoField(verbose_name='ID', auto_created=True, primary_key=True, serialize=False)),
                ('title', models.CharField(max_length=100, blank=True, null=True)),
                ('content', models.ImageField(blank=True, upload_to='uploads/%Y/%m/%d/', null=True)),
                ('meta', jsonfield.fields.JSONField(blank=True, default='', null=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('updated', models.DateTimeField(auto_now=True)),
                ('version', models.DecimalField(decimal_places=2, default=0, max_digits=4)),
                ('slugField', models.SlugField(max_length=200, unique=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Query',
            fields=[
                ('id', models.AutoField(verbose_name='ID', auto_created=True, primary_key=True, serialize=False)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('updated', models.DateTimeField(auto_now=True)),
                ('title', models.CharField(max_length=100, blank=True, default='')),
                ('SQL', models.TextField()),
                ('queryResults', jsonfield.fields.JSONField(default='')),
                ('owner', models.ForeignKey(related_name='query', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ('created',),
            },
        ),
        migrations.CreateModel(
            name='ReleaseType',
            fields=[
                ('id', models.AutoField(verbose_name='ID', auto_created=True, primary_key=True, serialize=False)),
                ('releaseTeam', models.CharField(max_length=100, choices=[('public', 'public'), ('team', 'team')])),
                ('dataRelease', models.CharField(max_length=100, choices=[('dr1', 'dr1'), ('dr2', 'dr2')])),
                ('slugField', models.SlugField(max_length=200, unique=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Spectrum',
            fields=[
                ('id', models.AutoField(verbose_name='ID', auto_created=True, primary_key=True, serialize=False)),
                ('title', models.CharField(max_length=100, blank=True, null=True)),
                ('content', models.ImageField(blank=True, upload_to='uploads/%Y/%m/%d/', null=True)),
                ('meta', jsonfield.fields.JSONField(blank=True, default='metadata', null=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('updated', models.DateTimeField(auto_now=True)),
                ('version', models.DecimalField(decimal_places=2, default=0, max_digits=4)),
                ('slugField', models.SlugField(max_length=200, unique=True, null=True)),
                ('release', models.ManyToManyField(to='restapi_app.ReleaseType', related_name='spectrum')),
            ],
        ),
        migrations.CreateModel(
            name='Survey',
            fields=[
                ('id', models.AutoField(verbose_name='ID', auto_created=True, primary_key=True, serialize=False)),
                ('title', models.CharField(max_length=100, unique=True, choices=[('gama', 'gama'), ('sami', 'sami')])),
            ],
        ),
        migrations.CreateModel(
            name='SurveyMetaData',
            fields=[
                ('id', models.AutoField(verbose_name='ID', auto_created=True, primary_key=True, serialize=False)),
                ('info', models.CharField(max_length=100)),
                ('survey', models.ForeignKey(related_name='surveymetadata', to='restapi_app.Survey')),
            ],
        ),
        migrations.AddField(
            model_name='releasetype',
            name='survey',
            field=models.ForeignKey(related_name='releasetype', to='restapi_app.Survey'),
        ),
        migrations.AddField(
            model_name='image',
            name='release',
            field=models.ManyToManyField(to='restapi_app.ReleaseType', related_name='image'),
        ),
        migrations.AddField(
            model_name='catalogue',
            name='catalogueGroup',
            field=models.ForeignKey(related_name='catalogue', to='restapi_app.CatalogueGroup'),
        ),
        migrations.AddField(
            model_name='catalogue',
            name='release',
            field=models.ManyToManyField(to='restapi_app.ReleaseType', related_name='catalogue'),
        ),
        migrations.AddField(
            model_name='astroobject',
            name='catalogue',
            field=models.ManyToManyField(to='restapi_app.Catalogue', related_name='astroobject'),
        ),
        migrations.AddField(
            model_name='astroobject',
            name='image',
            field=models.ManyToManyField(to='restapi_app.Image', related_name='astroobject'),
        ),
        migrations.AddField(
            model_name='astroobject',
            name='spectrum',
            field=models.ManyToManyField(to='restapi_app.Spectrum', related_name='astroobject'),
        ),
    ]
