#__author__ = 'lharischandra'


"""
Demonstrator web application showing a web interface to Spark for querying GAMA data.



"""

import os
import sys

# Imports for the web application
from bottle import route, request, default_app, static_file

from poc import HTML

import traceback

# Imports for Spark

# Add the PySpark packages to the module search path:
sys.path.extend(
    ['/Users/lharischandra/Code/spark-test/spark/python/lib/py4j-0.8.2.1-src.zip',
     '/Users/lharischandra/Code/spark-test/spark/python'])

import pyspark
import pyspark.sql.types as sparktypes
from pyspark.sql import SQLContext, HiveContext

#
os.environ["SPARK_HOME"] = '/Users/lharischandra/Code/spark-test/spark'
# This defines the application for WSGI purposes.
application = default_app()

SPARK = None

def get_spark():
    """Create (if necessary) and return the spark connection for this interpreter."""
    global SPARK
    if SPARK is None:
            SPARK = Spark()
    return SPARK

@route('/')
def index():
    """The default page shows the blank form.

    This serves the static page "queryform.html" which is in this directory.

    """

    # html = ""

    # # HTML To create a simple textarea with a submit button. Querty is GETed to /query
    # html += "<form action='query' method='get'>"
    # html += "<strong>Enter Query</strong></br>"
    # html += "<textarea name='query'></textarea></br>"
    # html += "<input type=\"submit\">"
    # html += "</form>"

    # return html

    # Find the path to the queryform (same directory as this script.)
    path = os.path.dirname(os.path.realpath(__file__))

    return static_file("queryform.html", root=path)

@route('/schema')
def schema():
    """Return a basic indication of the schema."""

    html = "<html><body><h1>Schema</h1>"
    for table in Spark.known_tables:
        html += "<h2>Table \"{}\"</h2>".format(table)
        html += "<dl>"
        for col in Spark.schema_info_for_table[table]:
            html += "<dt>{col}</dt><dd>{info}</dd>".format(
                col=col[0],
                info=col[2].__name__
                )
        html += "</dl>"
    html += "</body></html>"

    return html

@route('/hive-query')
def hive_query():
    #Return hive query results
    query_s = request.GET.get('hive-query', '').strip()

    if query_s == '':
        return "<p>No query given</p>"

    hive_ctx = get_spark().hivecontext
    query_rd = hive_ctx.sql(query_s)

    return query_rd

@route('/parquet-query')
def parquet_query():
    #Do a hive query
    query_s = request.GET.get('parquet-query', '').strip()
    sqlCtx = get_spark().sqlcontext

@route('/query')
def query():
    """Return the results from Spark of the given query.

    This is where the main query work is done.

    "Arguments" are taken as part of the HTTP GET request:

        query: string query to run

    Returns:
        If no query is given, then it simply returns a message to that effect.

        Otherwise, the query string is displayed.

    """

    query_string = request.GET.get('query', '').strip()
    version = request.GET.get('version', '').strip()

    if query_string == '':
        return "<p>No Query given</p>"

    html_output = ""

    # Display query'
    html_output += '<h2>Your Query</h2>'
    html_output += '<div class="geshifilter"><div class="text geshifilter-text" style="font-family:monospace;">'
    for line in query_string.splitlines(False):
        html_output += line + '<br />'
    html_output += '</div></div>'

    # Get query Result
    spark_connection = get_spark()
    result = spark_connection.spark_query(query_string)
    result_list = result.collect()

    # Display query result
    result_html = HTML.table(result_list,
            header_row=[i[0] for i in result.dtypes])
    html_output += result_html

    return html_output



class Spark(object):

    known_tables = ["DistancesFrames", "AATSpecAll"]

    schema_info_for_table = {
        "DistancesFrames":
            [
                ("CATID", sparktypes.IntegerType(), int),
                ("RA", sparktypes.DoubleType(), float),
                ("DEC", sparktypes.DoubleType(), float),
                ("NQ", sparktypes.IntegerType(), int),
                ("Z_HELIO", sparktypes.DoubleType(), float),
                ("Z_LG", sparktypes.DoubleType(), float),
                ("Z_CMB", sparktypes.DoubleType(), float),
                ("Z_TONRY", sparktypes.DoubleType(), float),
                ("Z_TONRY_HIGH", sparktypes.DoubleType(), float),
                ("Z_TONRY_LOW", sparktypes.DoubleType(), float),
                ("DM_70_30_70", sparktypes.DoubleType(), float),
                ("DM_100_30_70", sparktypes.DoubleType(), float),
                ("DM_100_27_75", sparktypes.DoubleType(), float)
            ],
        "AATSpecAll":
            [
                ("SPECID", sparktypes.StringType(), str),
                ("FIELDID", sparktypes.StringType(), str),
                ("RA", sparktypes.DoubleType(), float),
                ("DEC", sparktypes.DoubleType(), float),
                ("WMIN", sparktypes.DoubleType(), float),
                ("WMAX", sparktypes.DoubleType(), float),
                ("Z", sparktypes.DoubleType(), float),
                ("NQ", sparktypes.IntegerType(), int),
                ("PROB", sparktypes.DoubleType(), float),
                ("FIBRE", sparktypes.IntegerType(), int),
                ("DATE_OBS", sparktypes.StringType(), str),
                ("S_N", sparktypes.DoubleType(), float),
                ("PLATE", sparktypes.IntegerType(), int),
                ("X_POSN", sparktypes.IntegerType(), int),
                ("Y_POSN", sparktypes.IntegerType(), int),
                ("FILENAME", sparktypes.StringType(), str),
                ("URL", sparktypes.StringType(), str),
                ("URL_IMG", sparktypes.StringType(), str),
                ("CATID", sparktypes.IntegerType(), int),
                ("GAMA_NAME", sparktypes.StringType(), str),
                ("IC_FLAG", sparktypes.IntegerType(), int),
                ("DIST", sparktypes.DoubleType(), float),
                ("IS_SBEST", sparktypes.StringType(), str)
            ]
        }


    def __init__(self):
        # Load the Spark Connection and contexts:
        self.spark_conf = pyspark.SparkConf().setAppName("local_dev_test").setMaster("local")
        self.spark_context = pyspark.SparkContext(conf=self.spark_conf)
        self.sqlcontext = SQLContext(self.spark_context)
        self.hivecontext = HiveContext(self.spark_context)


        try:
            self.loaded_tables = set()
            # Load all tables into Spark:
            for table in self.known_tables:
                self.load_spark_table(table)
        except:
            tb = traceback.format_exc()
            print tb
            self.spark_context.stop()




    def load_spark_table(self, table):
        """Load the requested table into a SparkSQL DataFrame for querying.

        This is put together following the example at:
        http://spark.apache.org/docs/latest/sql-programming-guide.html#programmatically-specifying-the-schema

        """

        if table not in self.loaded_tables:
            spark_rdd = self.spark_context.textFile("hdfs://asvotest1.aao.gov.au:8020/user/hdfs/spark_poc/" + table)

            # Split each line of the CSV into individual fields (CSV data)
            parts = spark_rdd.map(lambda l: l.split(","))

            schema_info = self.schema_info_for_table[table]

            # Parse the data into the correct types:
            # def convert(parts):
            #     result = []
            #     for i, con in enumerate(schema_info):
            #         # con[2] will be the python type conversion function from schema_info_for_table
            #         result.append(con[2](parts[i]))

            # data = parts.map(convert)

            data = parts.map(
                lambda p:
                [con[2](p[i])
                    for i, con in enumerate(schema_info)]
                )

            schema = sparktypes.StructType(
                [sparktypes.StructField(i[0], i[1], True) for i in schema_info]
                )
            # Create dataframe and register it as a new table
            dataFrame = self.sqlcontext.createDataFrame(data, schema)
            dataFrame.registerTempTable(table)

            self.loaded_tables.add(table)

    def spark_query(self, query):
        """Perform a Spark SQL query."""

        results = self.sqlcontext.sql(query)

        return results

    def stop(self):
        self.spark_context.stop()

if __name__ == "__main__":
    # If the file is run from the command line, then we start the development
    # web server on the localhost at port 8000, and serve requests.
    from bottle import run, debug
    debug(True)
    run(reloader=False, host='0.0.0.0', port=8101)
    get_spark().stop()