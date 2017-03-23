import random, collections, logging
import json

import restapi_app.exceptions
import sys

import query.models
import query.serializers
import query.exceptions

import restapi_app.renderers
import restapi_app.renderers_custom.renderer_flat_csv

from rest_framework import generics, permissions, renderers, mixins, views, viewsets, status, mixins, exceptions
from rest_framework.response import Response
from django.contrib.auth.models import User
from django.conf import settings

from fidia.archive.asvo_spark import AsvoSparkArchive
from fidia.archive.presto import PrestoArchive
from asvo_database_backend_helpers import MappingDatabase

# log = logging.getLogger(__name__)
# log.setLevel(logging.DEBUG)


class Query(viewsets.ModelViewSet):
    """
    Create, update and destroy queries
    """
    serializer_class = query.serializers.QuerySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """
        Return a list of all queries for the currently authenticated user.
        """
        user = self.request.user
        return query.models.Query.objects.filter(owner=user).order_by('-updated')

    def perform_create(self, serializer):
        """
        Override CreateModelMixin perform_create to save object instance with ownership
        """
        serializer.save(owner=self.request.user)


class QuerySchema(views.APIView):
    """
    Retrieve the SQL schema for the ADC DB.

    asvo/query-schema/

    * Requires token authentication.
    * Only logged-in users are able to access this view.
    """
    # authentication_classes = (authentication.TokenAuthentication,)
    permission_classes = (permissions.AllowAny,)

    def get(self, request, format=None):
        # schema = PrestoArchive().get_sql_schema()
        schema = MappingDatabase.get_sql_schema()
        # schema = "test"
        return Response({"schema": schema})

#
# def run_sql_query(request_string):
#     try:
#         sample = AsvoSparkArchive().new_sample_from_query(request_string)
#     except KeyError:
#         return Response(status=status.HTTP_404_NOT_FOUND)
#     except:
#         # Catch java exception using system module which shows type, instance and traceback.
#         instance = sys.exc_info()[1]
#         raise query.exceptions.BadSQL("SQL Error: %s" % str(instance))
#
#     json_table = sample.tabular_data().reset_index().to_json(orient='split')
#     # Turned off capping data on the back end.
#     # The time issue is due to the browser rendering on the front end using dataTables.js.
#     # This view should still pass back *all* the data:
#     # http: // 127.0.0.1:8000/asvo/data/query/32/?format=json
#     # log.debug(json_table)
#     data = json.loads(json_table)
#     return data
#

# def get_sql_schema():
#     schema = PrestoArchive().get_sql_schema()
#     return json.dumps(schema)
#
#
# class QueryCreateView(viewsets.GenericViewSet, mixins.CreateModelMixin):
#     serializer_class = query.serializers.QuerySerializerCreateUpdate
#     permission_classes = [permissions.IsAuthenticated]
#     breadcrumb_list = []
#
#     class QueryCreateRenderer(restapi_app.renderers.ExtendBrowsableAPIRenderer):
#         """
#         Set template for Query Create view
#         """
#         template = 'query/query-create.html'
#
#     renderer_classes = [QueryCreateRenderer, renderers.JSONRenderer, restapi_app.renderers_custom.renderer_flat_csv.FlatCSVRenderer]
#
#     def get(self, request, format=None):
#         """
#         Return the blank form for a POST request
#         """
#         self.breadcrumb_list = ['New Query']
#         return Response()
#
#     def create(self, request, *args, **kwargs):
#         """
#         Create a model instance. Override CreateModelMixin create to catch the POST data for processing before save
#         Return only the location of the new resource in data['url'] as per HTTP spec.
#         """
#         self.breadcrumb_list = ['New Query']
#         saved_object = request.data
#         # Raise error if SQL field is empty
#         if "SQL" in saved_object:
#             if not saved_object["SQL"]:
#                 raise restapi_app.exceptions.CustomValidation("SQL Field Blank", 'detail', 400)
#             else:
#                 saved_object["queryResults"] = run_sql_query(request_string=saved_object["SQL"])
#                 # serializer = self.get_serializer(data=request.data)
#                 serializer = self.get_serializer(data=saved_object)
#                 serializer.is_valid(raise_exception=True)
#                 self.perform_create(serializer)
#                 headers = self.get_success_headers(serializer.data)
#                 # return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
#                 location_only = serializer.data
#                 location_only.clear()
#                 location_only['url'] = serializer.data['url']
#                 location_only['title'] = serializer.data['title']
#                 location_only['created'] = serializer.data['created']
#
#                 return Response(location_only, status=status.HTTP_201_CREATED, headers=headers)
#         else:
#             raise restapi_app.exceptions.CustomValidation("Incomplete request - SQL field missing", 'detail', 400)
#
#     def perform_create(self, serializer):
#         """
#         Override CreateModelMixin perform_create to save object instance with ownership
#         """
#         serializer.save(owner=self.request.user)
#
#
# class QueryListRetrieveUpdateDestroyView(viewsets.GenericViewSet, mixins.ListModelMixin,
#                                          mixins.RetrieveModelMixin, mixins.UpdateModelMixin, mixins.DestroyModelMixin):
#     serializer_class = query.serializers.QuerySerializerList
#     permission_classes = [permissions.IsAuthenticated]
#     breadcrumb_list = []
#
#     # descriptor decorator
#     @property
#     # renderer_classes = property(renderer_classes)
#     def renderer_classes(self):
#
#         if self.action == 'list':
#
#             class QueryListRenderer(restapi_app.renderers.ExtendBrowsableAPIRenderer):
#                 """
#                 Read-only query history
#                 """
#                 self.breadcrumb_list = ['Query History']
#                 template = 'query/query-list.html'
#
#             return [QueryListRenderer, renderers.JSONRenderer, restapi_app.renderers_custom.renderer_flat_csv.FlatCSVRenderer]
#         else:
#             class QueryRetrieveUpdateDestroyRenderer(restapi_app.renderers.ExtendBrowsableAPIRenderer):
#                 """
#                 Retrieve query instance
#                 """
#                 template = 'query/query-retrieve.html'
#             return [QueryRetrieveUpdateDestroyRenderer, renderers.JSONRenderer, restapi_app.renderers_custom.renderer_flat_csv.FlatCSVRenderer]
#
#     def get_queryset(self):
#         """
#         Query History.
#
#         This view should return a list of all queries for the currently authenticated user.
#         """
#         user = self.request.user
#         return query.models.Query.objects.filter(owner=user).order_by('-updated')
#
#     def get_serializer_class(self):
#         # Check the request type - if browser return truncated json
#         # If CSV/JSON return full payload.
#         serializer_class = query.serializers.QuerySerializerList
#         if self.action == 'list':
#             serializer_class = query.serializers.QuerySerializerList
#         if self.action == 'retrieve':
#             serializer_class = query.serializers.QuerySerializerRetrieve
#         if self.action == 'create' or self.action == 'update':
#             serializer_class = query.serializers.QuerySerializerCreateUpdate
#
#         return serializer_class
#
#     def get_renderer_context(self):
#         """
#         This can be set per view, useful for using the FlatCSVRenderer elsewhere.
#         Provide the particular json property you wish to be wrapped up, the relevant
#         column name and data name field
#         e.g., if your data looks as:
#         {'owner': 'lmannering', 'SQL': 'sdfsdfs', 'title': 'test', 'updated': '2016-05-03, 06:59:18', 'queryResults':
#             {'data': [[8823, 0.0499100015, 0.0163168724], [63147, 0.0499799997, 0.0380015143], [91963, 0.0499899983,
#             0.0106879927], [4, 2, 5], [3, 2, 1], [3, 3, 3], [1, 2, 2], [3, 1, 1]], 'columns': ['cataid', 'z', 'metal']},
#             'url': 'http://127.0.0.1:8000/asvo/data/query/32/?format=csv'}
#         """
#         context = super().get_renderer_context()
#         context['json_property_name'] = "queryResults"
#         context['data_name'] = 'data'
#         context['column_name'] = 'columns'
#         return context
#
#     def truncated_api_response_data(self, accepted_media_type, serialized_valid_data):
#         """
#         If the response is text/html (browsable api) then truncate to render limit and send flag info
#
#         """
#         # Make a copy of the data (already know is_valid() in create method)
#         new_serializer_data = serialized_valid_data
#
#         if accepted_media_type == 'text/html':
#             # Truncate response to browser but leave json and csv
#             query_results_rows = len(serialized_valid_data['queryResults']['index'])
#             query_results_cols = len(serialized_valid_data['queryResults']['columns'])
#             render_limit = 10000
#             # render_limit = 10
#
#             if query_results_cols * query_results_rows >= render_limit:
#                 # Get new row limit
#                 new_query_results_rows = int(render_limit / query_results_cols)
#                 # Truncate results
#                 new_data = serialized_valid_data['queryResults']['data'][0:new_query_results_rows]
#                 new_index = serialized_valid_data['queryResults']['index'][0:new_query_results_rows]
#                 new_serializer_data['queryResults']['data'] = new_data
#                 new_serializer_data['queryResults']['index'] = new_index
#                 new_serializer_data['flag'] = {'query_results_rows': query_results_rows, 'render_limit': render_limit,
#                                                'new_query_results_rows': new_query_results_rows}
#
#         return new_serializer_data
#
#     def retrieve(self, request, *args, **kwargs):
#         """ Retrieve a model instance. """
#         pk = request.parser_context['kwargs']['pk']
#         self.breadcrumb_list = ['Query History', pk]
#         instance = self.get_object()
#         serializer = self.get_serializer(instance)
#
#         return Response(self.truncated_api_response_data(accepted_media_type=request.accepted_media_type,
#                                                          serialized_valid_data=serializer.data))
#
#     def update(self, request, *args, **kwargs):
#         """
#         Update a model instance.
#         """
#         pk = request.parser_context['kwargs']['pk']
#         self.breadcrumb_list = ['Query History', pk]
#         partial = kwargs.pop('partial', False)
#         instance = self.get_object()
#
#         # current SQL
#         saved_object = instance
#         # inbound request
#         incoming_request = self.request.data
#
#         # if (incoming_request.data['queryResults'] != saved_object.queryResults):
#         #     raise PermissionDenied(
#         #         detail="WARNING - editing the query result is forbidden. Editable fields: title, SQL.")
#
#         # Override the incoming queryResults with the saved version
#         incoming_request['queryResults'] = saved_object.queryResults
#
#         # Update the SQL and queryResults
#         if incoming_request['SQL'] != saved_object.SQL:
#             incoming_request['queryResults'] = run_sql_query(request_string=incoming_request['SQL'])
#         serializer = self.get_serializer(instance, data=incoming_request, partial=partial)
#         serializer.is_valid(raise_exception=True)
#         self.perform_update(serializer)
#         return Response(serializer.data)
#
#     def perform_update(self, serializer):
#         serializer.save()
#
#     def partial_update(self, request, *args, **kwargs):
#         kwargs['partial'] = True
#         return self.update(request, *args, **kwargs)
#
#     def destroy(self, request, *args, **kwargs):
#         instance = self.get_object()
#         self.perform_destroy(instance)
#         return Response(status=status.HTTP_204_NO_CONTENT)
#
#     def perform_destroy(self, instance):
#         instance.delete()
