"""Generic Spark connector for the ASVO project.

This module, when loaded, will open a single connection to Spark (a
SparkContext) and also create a HiveContext as well. Repeated loading of the
module (e.g. in different places) will not create additional connections, but
instead use the same connection. (This module can be thought of as a Singleton
class.)

This is just a quick hack to support FIDIA external to the django application.

NOTE: The Spark paths are hard-coded below, but can be overridden by setting
the two environment variables $SPARK_HOME and $PYSPARK_PATH

"""

import sys
import os
import logging
log = logging.getLogger(__name__)

__author__ = "Andy Green"

SPARK_HOME = '/Users/agreen/Documents/ASVO/software/spark/spark-1.5.0-bin-hadoop2.6'
PYSPARK_PATH = ["/Users/agreen/Documents/ASVO/software/spark/spark-1.5.0-bin-hadoop2.6/python"]

try:
    SPARK_HOME = os.environ["SPARK_HOME"]
except KeyError:
    os.environ["SPARK_HOME"] = SPARK_HOME

try:
    PYSPARK_PATH = os.environ["PYSPARK_PATH"].split(":")
except KeyError:
    os.environ["PYSPARK_PATH"] = ":".join(PYSPARK_PATH)

sys.path.extend(PYSPARK_PATH)
# from pyspark import\
#     SparkConf, HiveContext, SparkContext
import pyspark

def singleton(cls):
    instance = cls()
    instance.__call__ = lambda: instance
    return instance

#SPARK_CONNECTOR = None

@singleton
class ASVOSparkConnector:

    def __init__(self):
        self._spark_context = None
        self._spark_conf = None
        self._hive_context = None


    def start_spark(self):
        if self._spark_context is not None:
            log.warn("Spark already started.")
        else:
            self._spark_conf = pyspark.SparkConf()# .setAppName("andy_jupyter").setMaster("local")
            self._spark_context = pyspark.SparkContext(conf=self._spark_conf)
            self._hive_context = pyspark.HiveContext(self._spark_context)

    @property
    def spark_context(self):
        if self._spark_context is None:
            self.start_spark()
        return self._spark_context

    @property
    def hive_context(self):
        if self._spark_context is None:
            self.start_spark()
        return self._hive_context


    def stop_spark(self):
        if self._spark_context is None:
            log.warn("Spark already stopped.")
        else:
            self._spark_context.stop()
            self._spark_conf = None
            self._spark_context = None
            self._hive_context = None
