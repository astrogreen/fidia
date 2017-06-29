from django.db import models


# Create your models here.
class Download(models.Model):
    created = models.DateTimeField(auto_now_add=True, editable=False)
    updated = models.DateTimeField(auto_now=True, editable=False)
    title = models.CharField(max_length=100, blank=False)
    data_list = models.TextField(blank=False)
    owner = models.ForeignKey('auth.User', related_name='download')
    is_completed = models.BooleanField(default=False, blank=False)
