from django.db import models
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver


class Contact(models.Model):
    name = models.CharField(max_length=100, blank=False)
    email = models.EmailField(max_length=100, blank=False)
    message = models.CharField(max_length=100, blank=False)


@receiver(pre_save, sender=Contact)
def email_contact_form(sender, instance, **kwargs):
    print("EMAIL CONTACT FORM")


class BugReport(models.Model):
    name = models.CharField(max_length=100, blank=False)
    email = models.EmailField(max_length=100, blank=False)
    message = models.CharField(max_length=10000, blank=False)
    url = models.CharField(max_length=100, blank=True)
    SURVEY_TEAM = (
        ('NA', 'Not applicable'),
        ('GAMA', 'GAMA'),
        ('SAMI', 'SAMI'),
        ('GALAH', 'GALAH'),
    )
    survey_team = models.CharField(choices=SURVEY_TEAM, default='NA', max_length=100)


@receiver(pre_save, sender=BugReport)
def email_bug_report(sender, instance, **kwargs):
    print("EMAIL BugReport FORM")
