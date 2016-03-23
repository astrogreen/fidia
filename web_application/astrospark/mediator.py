__author__ = 'lharischandra'
# from django.apps import apps
# Do spark related stuff here

from asvo_spark import ASVOSparkConnector


# appconf = apps.get_app_config('astrospark')
# sc = ASVOSparkConnector.spark_context
# hive_ctx = ASVOSparkConnector.hive_context

def execute_query(query):
    """
    Get spark sql context execute query and return results
    :param query: A hiveql query
    :return: A SparkSQL dataframe
    """

    return ASVOSparkConnector.hive_ctx.sql(query)

def stop_spark():
    """
    Stops spark context properly
    """
    ASVOSparkConnector.stop_spark()
    print('Spark stopped properly')


def get_column_names(table_id):
    """
    Returns the names of the table
    """
    df = ASVOSparkConnector.hive_context.sql('Select name from columns where tableid=' + str(table_id))
    return df.collect()

def get_tables():
    df = ASVOSparkConnector.hive_context.sql('Select name, tableid from tables where tableid is not null')
    return df.collect()
