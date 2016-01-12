# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('restapi_app', '0004_survey'),
    ]

    operations = [
        migrations.CreateModel(
            name='Products',
            fields=[
                ('id', models.AutoField(serialize=False, auto_created=True, verbose_name='ID', primary_key=True)),
                ('product', models.CharField(max_length=100, choices=[('img', 'img'), ('cat', 'cat'), ('spectra', 'spectra')])),
            ],
        ),
        migrations.CreateModel(
            name='Version',
            fields=[
                ('id', models.AutoField(serialize=False, auto_created=True, verbose_name='ID', primary_key=True)),
                ('version', models.CharField(default='dr2', max_length=50, choices=[('dr1', 'dr1'), ('dr2', 'dr2')])),
            ],
        ),
        migrations.DeleteModel(
            name='Survey',
        ),
    ]
