from django.db import models
from jsonfield import JSONField


class Query(models.Model):
    created = models.DateTimeField(auto_now_add=True, editable=False)
    updated = models.DateTimeField(auto_now=True, editable=False)
    title = models.CharField(max_length=100, blank=True, default="")
    SQL = models.TextField()
    queryResults = JSONField(default="")
    owner = models.ForeignKey('auth.User', related_name='query')

    class Meta:
        ordering = ('created',)