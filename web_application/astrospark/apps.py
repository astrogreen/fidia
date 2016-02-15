__author__ = 'lharischandra'
from django.apps import AppConfig
import os, sys
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

# Add the PySpark packages to the module search path:
if settings.SPARK_PATH:
    os.environ["PYSPARK_PATH"] = ":".join(settings.SPARK_PATH)
    #sys.path.extend(settings.SPARK_PATH)
else:
    raise ImproperlyConfigured("SPARK_PATH is not set.")

# Set spark home
if settings.SPARK_HOME:
    os.environ["SPARK_HOME"] = settings.SPARK_HOME
else:
    raise ImproperlyConfigured("SPARK_HOME is not set.")

#from pyspark import SparkConf, HiveContext, SparkContext

class SparkAppConfig(AppConfig):
    name = 'astrospark'
    verbose_name = "Spark Backend Application"

    def ready(self):
        # Initiate spark context here
        # self.spark_conf = SparkConf().setAppName("local_dev_test").setMaster("local")
        # self.spark_context = SparkContext(conf=self.spark_conf)
        # self.hivecontext = HiveContext(self.spark_context)
        pass

    def stop_spark(self):
        self.spark_context.stop()

    def get_spark_context(self):
        return self.spark_context

    def get_hive_context(self):
        return self.hivecontext