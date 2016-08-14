from django.db import models
from jsonfield import JSONField
from django.contrib.auth.models import User


class Download(models.Model):
    created = models.DateTimeField(auto_now_add=True, editable=False)
    updated = models.DateTimeField(auto_now=True, editable=False)
    title = models.CharField(max_length=100, blank=True, default="My Download")
    downloaditems = JSONField(default="", blank=False)
    owner = models.ForeignKey('auth.User', related_name='download')
    downloadlink = models.CharField(max_length=150, blank=True, default="in progress")
    size = models.CharField(max_length=30, blank=True, default="0")

    class Meta:
        ordering = ('created',)


class Storage(models.Model):
    storage_data = JSONField(default="", blank=True)
    owner = models.ForeignKey('auth.User', related_name='storage')
    created = models.DateTimeField(auto_now_add=True, editable=False)
    updated = models.DateTimeField(auto_now=True, editable=False)

