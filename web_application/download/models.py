from django.db import models
from jsonfield import JSONField
from django.contrib.auth.models import User


class Download(models.Model):
    created = models.DateTimeField(auto_now_add=True, editable=False)
    updated = models.DateTimeField(auto_now=True, editable=False)
    title = models.CharField(max_length=100, blank=True, default="My Download")
    # items = models.CharField(max_length=100, blank=True, default="My Items")
    items = JSONField(default="")
    owner = models.ForeignKey('auth.User', related_name='download')

    class Meta:
        ordering = ('created',)

