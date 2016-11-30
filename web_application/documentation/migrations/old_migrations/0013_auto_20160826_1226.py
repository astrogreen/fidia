# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('documentation', '0012_remove_topic_name'),
    ]

    operations = [
        migrations.RenameField(
            model_name='topic',
            old_name='topic_slug',
            new_name='slug',
        ),
    ]
