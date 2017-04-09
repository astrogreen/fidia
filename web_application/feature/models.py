from django.db import models
from vote.models import VoteModel


class Feature(models.Model):
    title = models.CharField(max_length=140, blank=False, default="Title")
    description = models.TextField(blank=False, max_length=1000, default="Long description goes here")

    def __str__(self):
        return '%s' % self.title


class Vote(VoteModel, models.Model):
    feature = models.ForeignKey(Feature, related_name='votes', blank=False)
    user = models.ForeignKey('auth.User', related_name='user')

    class Meta:
        unique_together = (("user", "feature"),)
