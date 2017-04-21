from __future__ import absolute_import, unicode_literals
import os
from celery import Celery
import logging

# set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'asvo.settings')

log = logging.getLogger(__name__)
# log.setLevel(logging.WARNING)

app = Celery('asvo')

# Using a string here means the worker don't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django app configs.
app.autodiscover_tasks()

@app.task(bind=True)
def debug_task(self):
    log.info('Request: {0!r}'.format(self.request))