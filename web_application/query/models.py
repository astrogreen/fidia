from django.db import models
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.contrib.postgres.fields import JSONField
from asvo_database_backend_helpers import MappingDatabase
from query.tasks import execute_query


class Query(models.Model):
    created = models.DateTimeField(auto_now_add=True, editable=False)
    owner = models.ForeignKey('auth.User', related_name='query')
    queryBuilderState = JSONField(blank=True, default="")

    # note - python dictionaries are mutable! default=dict()
    # is created once here, then any changes to new fields
    # alters the same instance. Instead, use the callable dict
    # as the default rather than the instance dict()
    results = JSONField(blank=True, default=dict)

    SQL = models.TextField(blank=False)
    title = models.CharField(max_length=1000, blank=True, default="My Query")
    updated = models.DateTimeField(auto_now=True, editable=False)
    isCompleted = models.BooleanField(default=False, blank=False)
    hasError = models.BooleanField(default=False, blank=False)
    error = JSONField(blank=True, default=dict)

    class Meta:
        ordering = ('created',)


# catch each Query's post_save signal and if successfully created (i.e, no validation
# issues with the instance), run async sql query on db.
@receiver(post_save, sender=Query)
def create_new_sql_query(sender, instance=None, created=False, **kwargs):
    if created:
        print('POST_SAVE SQL')
        print(instance)
        print(instance.SQL)
        print(instance.id)
        print(instance.owner.username)
        execute_query.delay(instance.SQL, instance.id)
        print("Handed sql task over to celery")


# If the SQL field has changed, execute query with new SQL
@receiver(pre_save, sender=Query)
def update_existing_query_instance(sender, instance, **kwargs):
    print("PRE_SAVE")
    try:
        obj = sender.objects.get(pk=instance.pk)
    except sender.DoesNotExist:
        pass  # Object is new, so field hasn't technically changed.
    else:
        if not obj.SQL == instance.SQL:  # SQL Field has changed
            print("PRE_SAVE SQL")
            execute_query.delay(instance.SQL, instance.id)
