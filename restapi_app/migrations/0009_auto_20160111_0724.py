# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('restapi_app', '0008_version'),
    ]

    operations = [
        migrations.CreateModel(
            name='Product',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, primary_key=True, auto_created=True)),
                ('product', models.CharField(choices=[('img', 'img'), ('cat', 'cat'), ('spectra', 'spectra')], max_length=100)),
            ],
        ),
        migrations.AlterField(
            model_name='version',
            name='version',
            field=models.CharField(choices=[('dr1', 'dr1'), ('dr2', 'dr2')], max_length=50),
        ),
        migrations.AddField(
            model_name='product',
            name='version',
            field=models.ForeignKey(to='restapi_app.Version'),
        ),
    ]
