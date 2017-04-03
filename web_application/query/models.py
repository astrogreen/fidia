from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from jsonfield import JSONField
from asvo_database_backend_helpers import MappingDatabase


class Query(models.Model):
    created = models.DateTimeField(auto_now_add=True, editable=False)
    owner = models.ForeignKey('auth.User', related_name='query')
    queryBuilderState = JSONField(blank=True, default="")
    results = JSONField(blank=True, default="")
    SQL = models.TextField(blank=False)
    title = models.CharField(max_length=100, blank=True, default="My Query")
    updated = models.DateTimeField(auto_now=True, editable=False)
    isCompleted = models.BooleanField(default=False)
    isInvalid = models.BooleanField(default=False)
    hasError = models.CharField(default="", blank=True, max_length=10000)

    class Meta:
        ordering = ('created',)


# catch each Query's post_save signal and if successfully created, run
# sql query on db
@receiver(post_save, sender=Query)
def create_new_sql_query(sender, instance=None, created=False, **kwargs):
    if created:
        print('RUN ASYNC SQL CODE')
        print(instance)
        print(instance.SQL)
        print(instance.id)
        print(instance.owner.username)
        # print(MappingDatabase.execute_adql_query(instance.SQL))
