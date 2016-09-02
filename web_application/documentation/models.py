from django.db import models
from jsonfield import JSONField
from django.db.models import Max
from django.utils.text import slugify


class Topic(models.Model):
    title = models.CharField(max_length=200, default='topic title')
    slug = models.SlugField(max_length=100, blank=False, unique=True)
    created = models.DateTimeField(auto_now_add=True, editable=False)
    updated = models.DateTimeField(auto_now=True, editable=False)
    ordering = models.IntegerField(unique=True)

    def save(self, *args, **kwargs):
        self.ordering = Topic.objects.aggregate(Max('ordering'))['ordering__max'] + 1

        self.slug = slugify(self.title)
        super(Topic, self).save(*args, **kwargs)

    def __str__(self):
        return "%s" % self.slug


class Article(models.Model):
    topic = models.ForeignKey(Topic, related_name='articles')
    title = models.CharField(max_length=200, default='article title')
    slug = models.SlugField(max_length=100, blank=False)
    content = models.TextField(max_length=100000, blank=False, default="Content")
    created = models.DateTimeField(auto_now_add=True, editable=False)
    updated = models.DateTimeField(auto_now=True, editable=False)
    image = models.ImageField(upload_to='articles/%Y/%m/%d', max_length=254, blank=True, null=True)
    image_caption = models.CharField(max_length=300, blank=True, null=True)

    def save(self, *args, **kwargs):
        self.slug = self.topic.slug + '-' + slugify(self.title)
        super(Article, self).save(*args, **kwargs)

    class Meta:
        unique_together = ('topic', 'slug')