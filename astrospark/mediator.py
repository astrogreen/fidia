__author__ = 'lharischandra'
from django.apps import apps
# Do spark related stuff here

def execute_query(query):
    """
    Get spark sql context execute query and return results
    :param query: A hiveql query
    :return: A SparkSQL dataframe
    """
    appconf = apps.get_app_config('astrospark')
    sc = appconf.get_spark_context()
    hive_ctx = appconf.get_hive_context()
    dataFrame = hive_ctx.sql(query)
    return dataFrame

def stop_spark():
    apps.get_app_config('astrospark').stop_spark()
    print('Spark stopped properly')
