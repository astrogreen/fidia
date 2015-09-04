__author__ = 'lharischandra'
from django.apps import AppConfig

class SparkAppConfig(AppConfig):
    name = 'astrospark'
    verbose_name = "Spark Backend Application"

    def ready(self):
        pass