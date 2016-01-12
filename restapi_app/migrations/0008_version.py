# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('restapi_app', '0007_auto_20160111_0530'),
    ]

    operations = [
        migrations.CreateModel(
            name='Version',
            fields=[
                ('id', models.AutoField(verbose_name='ID', auto_created=True, primary_key=True, serialize=False)),
                ('version', models.CharField(choices=[('dr1', 'dr1'), ('dr2', 'dr2')], default='dr2', max_length=50)),
                ('survey', models.ForeignKey(to='restapi_app.Survey')),
            ],
        ),
    ]
