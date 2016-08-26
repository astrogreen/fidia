from django.db import models
from jsonfield import JSONField


# A model per survey keeps the db tables separate and avoids naming collisions with the slugs when enforcing uniqueness
# e.g., docs/sami/trait-doc and docs/gama/trait-doc


class Topic(models.Model):
    title = models.CharField(max_length=200, default='topic title')
    slug = models.SlugField(max_length=100, blank=False, unique=True)

    def __str__(self):
        return "%s" % self.slug


class Article(models.Model):
    topic = models.ForeignKey(Topic, related_name='articles')
    title = models.CharField(max_length=200, default='article title')
    slug = models.SlugField(max_length=100, blank=False, unique=True)
    content = models.TextField(max_length=100000, blank=False, default="Content")

    class Meta:
        unique_together = ('topic', 'slug')






class SAMI(models.Model):
    created = models.DateTimeField(auto_now_add=True, editable=False)
    updated = models.DateTimeField(auto_now=True, editable=False)
    title = models.CharField(max_length=100, blank=False, default="Document Title")
    content = models.TextField(max_length=100000, blank=False, default="Content")
    slug = models.SlugField(max_length=100, blank=False, unique=True)
    route_name = models.CharField(max_length=100, blank=False, default='documentation:sami-docs-detail')

    def get_route_name(self):
        return 'documentation:sami-docs-detail'


class GAMA(models.Model):
    created = models.DateTimeField(auto_now_add=True, editable=False)
    updated = models.DateTimeField(auto_now=True, editable=False)
    title = models.CharField(max_length=100, blank=False, default="Document Title")
    content = models.TextField(max_length=100000, blank=False, default="Content")
    slug = models.SlugField(max_length=100, blank=False, unique=True)
    route_name = models.CharField(max_length=100, blank=False, default='')


class AAODC(models.Model):
    created = models.DateTimeField(auto_now_add=True, editable=False)
    updated = models.DateTimeField(auto_now=True, editable=False)
    title = models.CharField(max_length=100, blank=False, default="Document Title")
    content = models.TextField(max_length=100000, blank=False, default="Content")
    slug = models.SlugField(max_length=100, blank=False, unique=True)
    route_name = models.CharField(max_length=100, blank=False, default='')
