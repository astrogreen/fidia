from django.db import models
from jsonfield import JSONField
from datetime import datetime

DATA_RELEASES = [('dr1', 'dr1'), ('dr2', 'dr2')]
SURVEYS = [('gama', 'gama'), ('sami', 'sami')]
PRODUCTS = [('img', 'img'), ('cat', 'cat'), ('spectra','spectra')]


class Query(models.Model):
    created = models.DateTimeField(auto_now_add=True, editable=False)
    updated = models.DateTimeField(auto_now=True, editable=False)
    title = models.CharField(max_length=100, blank=True, default="")
    SQL = models.TextField()
    queryResults = JSONField(default="")
    owner = models.ForeignKey('auth.User', related_name='query')

    class Meta:
        ordering = ('created',)



class Survey(models.Model):
    survey = models.CharField(choices=SURVEYS, max_length=100)


class Version(models.Model):
    version = models.CharField(choices=DATA_RELEASES, max_length=50)
    survey = models.ForeignKey(Survey, related_name='version')
    #defines many to one relationship


class Product(models.Model):
    product = models.CharField(choices=PRODUCTS, max_length=100)
    version = models.ForeignKey(Version)


