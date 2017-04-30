from django.db import models
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver


class Contact(models.Model):
    name = models.CharField(max_length=100, blank=False)
    email = models.EmailField(max_length=100, blank=False)
    message = models.CharField(max_length=100, blank=False)


# If the SQL field has changed, execute query with new SQL
@receiver(pre_save, sender=Contact)
def update_existing_query_instance(sender, instance, **kwargs):
    print("EMAIL CONTACT FORM")

#     try:
#         obj = sender.objects.get(pk=instance.pk)
#     except sender.DoesNotExist:
#         pass  # Object is new, so field hasn't technically changed.
#     else:
#         if not obj.SQL == instance.SQL:  # SQL Field has changed
#             print("PRE_SAVE SQL")
#             execute_query.delay(instance.SQL, instance.id)
