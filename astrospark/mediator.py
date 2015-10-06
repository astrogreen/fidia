__author__ = 'lharischandra'
from django.apps import apps
# Do spark related stuff here

appconf = apps.get_app_config('astrospark')
sc = appconf.get_spark_context()
hive_ctx = appconf.get_hive_context()

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
    appconf.stop_spark()
    print('Spark stopped properly')


def get_column_names(table):
    """
    Returns the names of the table
    """
    return hive_ctx.table(table).columns

def get_tables():
    return hive_ctx.tableNames()
