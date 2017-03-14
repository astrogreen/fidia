from django.db import models
from jsonfield import JSONField


class Query(models.Model):
    created = models.DateTimeField(auto_now_add=True, editable=False)
    owner = models.ForeignKey('auth.User', related_name='query')
    queryBuilderState = JSONField(blank=True, default="")
    results = JSONField(blank=True, default={})
    SQL = models.TextField(blank=False)
    title = models.CharField(max_length=100, blank=True, default="My Query")
    updated = models.DateTimeField(auto_now=True, editable=False)
    isCompleted = models.BooleanField(default=False)

    class Meta:
        ordering = ('created',)


