from django.db import models


# A model per survey keeps the db tables separate and avoids naming collisions with the slugs when enforcing uniqueness
# e.g., docs/sami/trait-doc and docs/gama/trait-doc
class SAMI(models.Model):
    created = models.DateTimeField(auto_now_add=True, editable=False)
    updated = models.DateTimeField(auto_now=True, editable=False)
    title = models.CharField(max_length=100, blank=False, default="Document Title")
    content = models.TextField(max_length=100000, blank=False, default="Content")
    slug = models.SlugField(max_length=100, blank=False, unique=True)


class GAMA(models.Model):
    created = models.DateTimeField(auto_now_add=True, editable=False)
    updated = models.DateTimeField(auto_now=True, editable=False)
    title = models.CharField(max_length=100, blank=False, default="Document Title")
    content = models.TextField(max_length=100000, blank=False, default="Content")
    slug = models.SlugField(max_length=100, blank=False, unique=True)


class AAODC(models.Model):
    created = models.DateTimeField(auto_now_add=True, editable=False)
    updated = models.DateTimeField(auto_now=True, editable=False)
    title = models.CharField(max_length=100, blank=False, default="Document Title")
    content = models.TextField(max_length=100000, blank=False, default="Content")
    slug = models.SlugField(max_length=100, blank=False, unique=True)


