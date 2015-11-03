__author__ = 'lharischandra'
from django.apps import apps
# Do spark related stuff here

from fidia import asvo_spark


appconf = apps.get_app_config('astrospark')
sc = asvo_spark.spark_context
hive_ctx = asvo_spark.hive_context

def execute_query(query):
    """
    Get spark sql context execute query and return results
    :param query: A hiveql query
    :return: A SparkSQL dataframe
    """

    return hive_ctx.sql(query)

def stop_spark():
    """
    Stops spark context properly
    """
    asvo_spark.stop_spark()
    print('Spark stopped properly')


def get_column_names(table):
    """
    Returns the names of the table
    """
    return hive_ctx.table(table).columns

def get_tables():
    df = hive_ctx.sql('Select name from tables where tableid is not null')
    return df.collect()
