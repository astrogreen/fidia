# Create your tasks here
from __future__ import absolute_import, unicode_literals
from celery import shared_task
from asvo_database_backend_helpers import MappingDatabase, PrestDBException
import json
import logging
import traceback
from py4j.protocol import Py4JError, Py4JJavaError, Py4JNetworkError

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)

@shared_task
def execute_query(query, query_id, results_tbl):
    # here we need to actually call prestodb with the query.
    try:
        result = MappingDatabase.execute_adql_query(query, results_tbl)
        if result is not None:
            query = 'Update query_query set "is_completed" = {0} where id={1};'.format(True, query_id)
            MappingDatabase.execute_sql_query(query, True)
        else:
            log.info("No results to save.")
    except (Exception) as ex:
        errors = dict()
        if(isinstance(ex, Py4JJavaError)):
            errors['humanMessage'] = ex.java_exception.toString()
            errors['message'] = traceback.format_exc()
            errors['code'] = 501
        elif(isinstance(ex, Py4JNetworkError)):
            errors['humanMessage'] = str(ex)
            errors['message'] = traceback.format_exc()
            errors['code'] = 503
        elif(isinstance(ex, Py4JError)):
            errors['humanMessage'] = str(ex)
            errors['message'] = traceback.format_exc()
            errors['code'] = 501
        elif(isinstance(ex, ConnectionError)):
            errors['humanMessage'] = str(ex)
            errors['message'] = traceback.format_exc()
            errors['code'] = 503
        elif(isinstance(ex, PrestDBException)):
            errors['humanMessage'] = ex.message
            errors['message'] = ex.message
            errors['code'] = ex.status_code
        else:
            errors['humanMessage'] = str(ex)
            errors['message'] = traceback.format_exc()
            errors['code'] = 500
        query = 'Update query_query set "has_error" = {0}, error = \'{1}\' where id={2};'.format(
                True, json.dumps(errors), query_id)
        MappingDatabase.execute_sql_query(query, True)



