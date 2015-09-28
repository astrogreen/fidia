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

__author__ = "Andy Green"

SPARK_HOME = '/Users/agreen/Documents/ASVO/software/spark/spark-1.5.0-bin-hadoop2.6'
PYSPARK_PATH = ["/Users/agreen/Documents/ASVO/software/spark/spark-1.5.0-bin-hadoop2.6/python"]

import sys

import os

try:
    SPARK_HOME = os.environ["SPARK_HOME"]
except KeyError:
    os.environ["SPARK_HOME"] = SPARK_HOME

try:
    PYSPARK_PATH = os.environ["PYSPARK_PATH"]
except KeyError:
    PYSPARK_PATH = ["/Users/agreen/Documents/ASVO/software/spark/spark-1.5.0-bin-hadoop2.6/python"]


sys.path.extend(PYSPARK_PATH)
from pyspark import SparkConf, HiveContext, SparkContext

spark_conf = None
spark_context = None
hive_context = None

class LocalSparkContext(SparkContext):
    def stop(self):
        stop_spark()

def start_spark_context():
    global spark_conf
    global spark_context 
    global hive_context
    if spark_context is not None:
        print("Spark already started.")
    else:
        spark_conf = SparkConf().setAppName("andy_jupyter").setMaster("local")
        spark_context = LocalSparkContext(conf=spark_conf)
        hive_context = HiveContext(spark_context)

def stop_spark():
    global spark_conf
    global spark_context 
    global hive_context
    if spark_context is None:
        print("Spark already stopped.")
    else:
        super(LocalSparkContext, spark_context).stop()
        spark_conf = None
        spark_context = None
        hive_context = None

# We assume that when this module is imported, the spark context should be started up.
start_spark_context()