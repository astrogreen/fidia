import logging
from django.utils.text import slugify
import numpy as np
from rest_framework import permissions, views, viewsets, mixins, generics
from rest_framework.response import Response
from rest_framework.decorators import detail_route

# from rest_framework.settings import api_settings
# from rest_framework_csv import renderers as r
# from django.contrib.auth.models import User
from django.conf import settings

import query.models
import query.serializers
import query.exceptions
import query.renderers

import query.dummy_schema

# import restapi_app.renderers
# import restapi_app.renderers_custom.renderer_flat_csv
#
# from fidia.archive.asvo_spark import AsvoSparkArchive
# from fidia.archive.presto import PrestoArchive
from asvo_database_backend_helpers import MappingDatabase

log = logging.getLogger(__name__)
# log.setLevel(logging.DEBUG)


class Query(viewsets.ModelViewSet):
    """
    Create, update and destroy queries
    """
    serializer_class = query.serializers.QueryListSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = None
    # renderer_classes = tuple(api_settings.DEFAULT_RENDERER_CLASSES) + (query.renderers.MyCSVQueryRenderer,)

    serializer_action_classes = {
        'list': query.serializers.QueryListSerializer,
        'retrieve': query.serializers.QueryRetrieveSerializer,
        'create': query.serializers.QueryCreateSerializer,
        'update': query.serializers.QueryCreateSerializer,
        'destroy': query.serializers.QueryRetrieveSerializer,
    }

    def get_serializer_class(self):
        try:
            return self.serializer_action_classes[self.action]
        except (KeyError, AttributeError):
            return super(Query, self).get_serializer_class()

    def get_queryset(self):
        """
        Return a list of all queries for the currently authenticated user.
        """
        user = self.request.user
        return query.models.Query.objects.filter(owner=user).exclude(pk=32).order_by('-updated')

    def perform_create(self, serializer):
        """
        Override CreateModelMixin perform_create to save object instance with ownership
        """
        serializer.save(owner=self.request.user)

    def finalize_response(self, request, response, *args, **kwargs):
        """
        Set filename as title provided by the user
        """
        response = super(Query, self).finalize_response(request, response, *args, **kwargs)
        if response.accepted_renderer.format == 'csv':
            title = "query_result"
            if hasattr(response, "data") and "title" in response.data:
                if response.data["title"] is not None:
                    title = slugify(response.data["title"])
            response['content-disposition'] = 'attachment; filename=%s.csv' % title
        return response

    @detail_route()
    def result(self, request, *args, **kwargs):
        """
        Get the top X number of rows from the table_name results table
        to display to the user on the front end.
        Args:
            request: 
            *args: 
            **kwargs: 

        Returns:

        """
        obj = self.get_object()
        data = np.random.random((1000, 5))
        dummy_results = {
            "data": data,
            "columns": [
                {"name": "StellarMasses_CATAID", "type": "integer",
                 "typeSignature": {"rawType": "integer", "arguments": [], "typeArguments": [],
                                   "literalArguments": []}},
                {"name": "StellarMasses_Z", "type": "double",
                 "typeSignature": {"rawType": "double",
                                   "arguments": [],
                                   "typeArguments": [],
                                   "literalArguments": []}},
                {"name": "StellarMasses_nQ", "type": "integer",
                 "typeSignature": {"rawType": "integer", "arguments": [], "typeArguments": [],
                                   "literalArguments": []}},
                {"name": "StellarMasses_SURVEY_CODE", "type": "integer",
                 "typeSignature": {"rawType": "integer", "arguments": [], "typeArguments": [],
                                   "literalArguments": []}},
                {"name": "StellarMasses_Z_TONRY", "type": "double",
                 "typeSignature": {"rawType": "double",
                                   "arguments": [],
                                   "typeArguments": [],
                                   "literalArguments": []}}
            ]}

        # Retrieve the top 1000 rows from the table
        if obj.is_completed and not obj.is_expired and obj.table_name:
            if settings.DB_LOCAL:
                data = dummy_results
            else:
                data = MappingDatabase.get_results_table(name=obj.table_name, length=1000)
        else:
            data = None
        return Response(data)


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
        if settings.DB_LOCAL:
            schema = query.dummy_schema.DUMMY_SCHEMA
        else:
            schema = MappingDatabase.get_sql_schema()
        return Response(schema)


class QueryResultTables(object):
    def __init__(self, **kwargs):
        for field in ('id', 'col1', 'col2', 'col3'):
            setattr(self, field, kwargs.get(field, None))

# results = {
#     1: QueryResultTables(id=1, col1='Demo', col2='xordoquy', col3='Done'),
#     2: QueryResultTables(id=2, col1='Model less demo', col2='xordoquy', col3='Ongoing'),
#     3: QueryResultTables(id=3, col1='Sleep more', col2='xordoquy', col3='New'),
# }
#
# results = {}
# for i in range(0, 200):
#     data = {}
#     for y in range(0, 200):
#         data[y] = {'col1': 'testrow1', 'col2': 'testrow1'}
#
#     results[i] = {
#         'id': i,
#         'data': data
#     }
    # results[i] = QueryResultTables(id=i, col1='test', col2='test', col3='Done'),


# class Result(viewsets.GenericViewSet):
#       testing
#     serializer_class = query.serializers.ResultListSerializer
#     queryset = results
#
#     def list(self, request):
#         queryset = list(results.values())
#         page = self.paginate_queryset(queryset)
#
#         if page is not None:
#             serializer = query.serializers.ResultListSerializer(page, many=True)
#             return self.get_paginated_response(serializer.data)
#
#         serializer = query.serializers.ResultListSerializer(instance=queryset, many=True)
#         return Response(serializer.data)
#
#     def retrieve(self, request, pk=None, *args, **kwargs):
#         instance = results.get(int(pk))['data']
#         queryset = list(instance.values())
#         page = self.paginate_queryset(queryset)
#
#         if page is not None:
#             serializer = query.serializers.ResultRetrieveSerializer(page, many=True)
#             return self.get_paginated_response(serializer.data)
#
#         serializer = query.serializers.ResultRetrieveSerializer(instance=queryset, many=True)
#         return Response(serializer.data)


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
