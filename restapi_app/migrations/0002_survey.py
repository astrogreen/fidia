# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('restapi_app', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Survey',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False, auto_created=True, verbose_name='ID')),
                ('version', models.CharField(default='dr2', max_length=50, choices=[('dr1', 'dr1'), ('dr2', 'dr2')])),
            ],
        ),
    ]
