# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('restapi_app', '0003_delete_survey'),
    ]

    operations = [
        migrations.CreateModel(
            name='Survey',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', primary_key=True, auto_created=True)),
                ('version', models.CharField(default='dr2', choices=[('dr1', 'dr1'), ('dr2', 'dr2')], max_length=50)),
            ],
        ),
    ]
