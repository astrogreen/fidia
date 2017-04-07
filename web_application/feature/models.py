from django.db import models


# Create your models here.
class Feature(models.Model):
    name = models.CharField(blank=False, max_length=100)
    description = models.TextField(blank=False, max_length=1000)
    votes = models.IntegerField(default=1)
    priority = models.IntegerField(default=0)
