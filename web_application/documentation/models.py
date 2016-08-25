from django.db import models


# Create your models here.
class Documentation(models.Model):
    created = models.DateTimeField(auto_now_add=True, editable=False)
    updated = models.DateTimeField(auto_now=True, editable=False)
    title = models.CharField(max_length=100, blank=False, default="Document Title")
    content = models.TextField(max_length=100000, blank=False, default="Content")
    slug = models.SlugField(max_length=20, blank=False, unique=True)
