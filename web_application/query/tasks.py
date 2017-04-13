# Create your tasks here
from __future__ import absolute_import, unicode_literals
from celery import shared_task
from asvo_database_backend_helpers import MappingDatabase
import json

@shared_task
def execute_query(query, query_id):
    # here we need to actually call prestodb with the query.
    #query = "Select InputCat__InputCatA__CATAID as CATAID, InputCat__InputCatA__RA as RA from gama_mega_table where InputCat__InputCatA__DEC > 0.234"
    result = MappingDatabase.execute_adql_query(query)
    print("Executed successfully. Finishing the task")

    if result is not None:
        # print(result)
        qry = "Update query_query set isCompleted = {0}, results = '{1}' where id={2};".format(
                1, json.dumps(result), query_id)
        # print(qry)
        MappingDatabase.execute_sql_query(qry)
    else:
        print("Error occurred")
