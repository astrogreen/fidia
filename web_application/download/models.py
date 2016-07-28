from django.db import models
from jsonfield import JSONField
from django.contrib.auth.models import User


class Download(models.Model):
    created = models.DateTimeField(auto_now_add=True, editable=False)
    updated = models.DateTimeField(auto_now=True, editable=False)
    title = models.CharField(max_length=100, blank=True, default="My Download")
    # items = models.CharField(max_length=2000, blank=False, default="")
    items = JSONField(default="", blank=False)
    owner = models.ForeignKey('auth.User', related_name='download')
    downloadlink = models.CharField(max_length=150, blank=True, default="In Progress")

    class Meta:
        ordering = ('created',)

