import random, collections, logging
import json
from pprint import pprint
from .permissions import IsNotAuthenticated
from .exceptions import NoPropertyFound, CustomValidation

from .models import (
    Query,
)
from .serializers import (
    CreateUserSerializer,
    UserSerializer,
    ContactFormSerializer,
    QuerySerializerCreateUpdate, QuerySerializerList, QuerySerializerRetrieve,
    SampleSerializer,
    AstroObjectSerializer,
    AstroObjectTraitSerializer,
    AstroObjectTraitPropertySerializer,
    SOVListSurveysSerializer,
    SOVRetrieveObjectSerializer
)
import restapi_app.renderers

from .renderers import (
    FITSRenderer,
    SOVListRenderer,
    SOVDetailRenderer,
    QueryRenderer,
    AstroObjectRenderer,
    GAMARenderer,
    # SAMIRenderer,
    SampleRenderer,
    RegisterRenderer,
    TraitRenderer,
    TraitPropertyRenderer
)

from .renderers_custom.renderer_flat_csv import FlatCSVRenderer

from rest_framework import generics, permissions, renderers, mixins, views, viewsets, status, mixins, exceptions
from rest_framework.response import Response
from django.contrib.auth.models import User
from rest_framework_csv import renderers as r

from django.conf import settings

from fidia.archive.asvo_spark import AsvoSparkArchive

log = logging.getLogger(__name__)
# log.setLevel(logging.DEBUG)


class CreateUserView(generics.ListCreateAPIView):
    """
    User View to allow registration
    """
    model = User
    permission_classes = [IsNotAuthenticated]
    serializer_class = CreateUserSerializer
    renderer_classes = [restapi_app.renderers.QueryCreateRenderer, renderers.JSONRenderer]

    def get_queryset(self):
        queryset = User.objects.none()
        return queryset


class QueryHistoryView(mixins.ListModelMixin, viewsets.GenericViewSet):
    serializer_class = QuerySerializerList
    permission_classes = [permissions.IsAuthenticated]
    renderer_classes = [restapi_app.renderers.QueryListRenderer, renderers.JSONRenderer]

    def get_queryset(self):
        """
        Query History.

        This view should return a list of all queries
        for the currently authenticated user.
        """
        user = self.request.user
        return Query.objects.filter(owner=user).order_by('-updated')


class QueryCreateView(viewsets.GenericViewSet, mixins.CreateModelMixin):
    serializer_class = QuerySerializerCreateUpdate
    permission_classes = [permissions.IsAuthenticated]
    renderer_classes = [restapi_app.renderers.QueryCreateRenderer, renderers.JSONRenderer, FlatCSVRenderer]

    def get(self, request, format=None):
        """
        Return the blank form for a POST request
        """
        return Response()

    def run_fidia(self, request_string):

        # SELECT t1.CATAID FROM InputCatA AS t1 WHERE t1.CATAID  BETWEEN 65401 and 65410
        sample = AsvoSparkArchive().new_sample_from_query(request_string)

        # (json_n_rows, json_n_cols) = sample.tabular_data().shape
        # json_element_cap = 100000
        # json_row_cap = 2000

        json_table = sample.tabular_data().reset_index().to_json(orient='split')

        # Turned off capping data on the back end. The time issue is due to the
        # browser rendering on the front end using dataTables.js.
        # This view should still pass back *all* the data:
        # http: // 127.0.0.1:8000/asvo/data/query/32/?format=json

        # if (json_n_rows*json_n_cols < json_element_cap ):
        #     json_table = sample.tabular_data().reset_index().to_json(orient='split')
        #     json_flag = 0
        # else:
        #     # json_table = sample.tabular_data().reset_index().to_json(orient='split')
        #     json_table = sample.tabular_data().iloc[:json_row_cap].reset_index().to_json(orient='split')
        #     json_flag = json_row_cap

        log.debug(json_table)
        data = json.loads(json_table)

        return data

    def create(self, request, *args, **kwargs):
        """
        Create a model instance. Override CreateModelMixin create to catch the POST data for processing before save
        Return only the location of the new resource in data['url'] as per HTTP spec.
        """
        saved_object = request.data
        # Raise error if SQL field is empty
        if "SQL" in saved_object:
            if not saved_object["SQL"]:
                raise CustomValidation("SQL Field Blank", 'detail', 400)
            else:
                saved_object["queryResults"] = self.run_fidia(saved_object["SQL"])
                # serializer = self.get_serializer(data=request.data)
                serializer = self.get_serializer(data=saved_object)
                serializer.is_valid(raise_exception=True)
                self.perform_create(serializer)
                headers = self.get_success_headers(serializer.data)
                # return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
                location_only = serializer.data
                location_only.clear()
                location_only['url'] = serializer.data['url']
                location_only['title'] = serializer.data['title']
                location_only['created'] = serializer.data['created']

                return Response(location_only, status=status.HTTP_201_CREATED, headers=headers)
        else:
            raise CustomValidation("SQL Field Blank", 'detail', 400)

    def perform_create(self, serializer):
        """
        Override CreateModelMixin perform_create to save object instance with ownership
        """
        serializer.save(owner=self.request.user)


class QueryRetrieveUpdateDestroyView(viewsets.GenericViewSet, mixins.RetrieveModelMixin, mixins.UpdateModelMixin,
                                     mixins.DestroyModelMixin):
    serializer_class = QuerySerializerList
    permission_classes = [permissions.IsAuthenticated]
    renderer_classes = [restapi_app.renderers.QueryRetrieveUpdateDestroyRenderer, renderers.JSONRenderer, FlatCSVRenderer]

    def get_queryset(self):
        """
        Query Retrieve.

        This view should return a single query of id = pk
        for the currently authenticated user.
        """
        user = self.request.user
        # id = self.request['pk']
        return Query.objects.filter(owner=user)
        # return Query.objects.filter(owner=user).filter(id=id)



    def get_serializer_class(self):
        # Check the request type - if browser return truncated json
        # If CSV/JSON return full payload.
        serializer_class = QuerySerializerList
        if self.action == 'list':
            serializer_class = QuerySerializerList
        if self.action == 'retrieve':
            serializer_class = QuerySerializerRetrieve
        if self.action == 'create' or self.action == 'update':
            serializer_class = QuerySerializerCreateUpdate

        return serializer_class

    def truncated_api_response_data(self, accepted_media_type, serialized_valid_data):
        """
        If the response is text/html (browsable api) then truncate to render limit and send flag info

        """
        # Make a copy of the data (already know is_valid() in create method)
        new_serializer_data = serialized_valid_data

        if accepted_media_type == 'text/html':
            # Truncate response to browser but leave json and csv
            query_results_rows = len(serialized_valid_data['queryResults']['index'])
            query_results_cols = len(serialized_valid_data['queryResults']['columns'])
            render_limit = 10000
            # render_limit = 10

            if query_results_cols * query_results_rows >= render_limit:
                # Get new row limit
                new_query_results_rows = int(render_limit / query_results_cols)
                # Truncate results
                new_data = serialized_valid_data['queryResults']['data'][0:new_query_results_rows]
                new_index = serialized_valid_data['queryResults']['index'][0:new_query_results_rows]
                new_serializer_data['queryResults']['data'] = new_data
                new_serializer_data['queryResults']['index'] = new_index
                new_serializer_data['flag'] = {'query_results_rows': query_results_rows, 'render_limit': render_limit,
                                               'new_query_results_rows': new_query_results_rows}

        return new_serializer_data

    def retrieve(self, request, *args, **kwargs):
        """ Retrieve a model instance. """
        instance = self.get_object()
        serializer = self.get_serializer(instance)

        return Response(self.truncated_api_response_data(accepted_media_type=request.accepted_media_type,
                                                         serialized_valid_data=serializer.data))

    def update(self, request, *args, **kwargs):
        """
        Update a model instance.
        """
        partial = kwargs.pop('partial', False)
        instance = self.get_object()

        # current SQL
        saved_object = instance
        # inbound request
        incoming_object = self.request.data

        # override the incoming queryResults with the saved version
        incoming_object['queryResults'] = (saved_object.queryResults)

        # if new sql (and/or results have been tampered with), re-run fidia and override results
        # if (incoming_object['SQL'] != saved_object.SQL) or (testQueryResultsTamper.data['queryResults'] != saved_object.queryResults):
        if incoming_object['SQL'] != saved_object.SQL:
            # if (testQueryResultsTamper.data['queryResults'] != saved_object.queryResults):
            #     pprint('qR changed')
            #     raise PermissionDenied(detail="WARNING - editing the query result is forbidden. Editable fields: title, SQL.")
            incoming_object['queryResults'] = self.run_FIDIA(self.request.data)
            pprint('update object')

        serializer = self.get_serializer(instance, data=incoming_object, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)

    def perform_update(self, serializer):
        serializer.save()

    def partial_update(self, request, *args, **kwargs):
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def perform_destroy(self, instance):
        instance.delete()


class QueryViewSet(viewsets.ModelViewSet):
    """
    Query the AAO Data Archive
    """
    serializer_class = QuerySerializerList
    permission_classes = [permissions.IsAuthenticated]
    queryset = Query.objects.all()

    renderer_classes = [QueryRenderer, renderers.JSONRenderer, FlatCSVRenderer]

    def get_renderer_context(self):
        """
        This can be set per view, useful for using the FlatCSVRenderer elsewhere.
        Provide the particular json property you wish to be wrapped up, the relevant
        column name and data name field
        e.g., if your data looks as:
        {'owner': 'lmannering', 'SQL': 'sdfsdfs', 'title': 'test', 'updated': '2016-05-03, 06:59:18', 'queryResults':
            {'data': [[8823, 0.0499100015, 0.0163168724], [63147, 0.0499799997, 0.0380015143], [91963, 0.0499899983,
            0.0106879927], [4, 2, 5], [3, 2, 1], [3, 3, 3], [1, 2, 2], [3, 1, 1]], 'columns': ['cataid', 'z', 'metal']},
            'url': 'http://127.0.0.1:8000/asvo/data/query/32/?format=csv'}
        """
        context = super().get_renderer_context()
        context['json_property_name'] = "queryResults"
        context['data_name'] = 'data'
        context['column_name'] = 'columns'
        return context

    def get_serializer_class(self):
        # Check the request type - if browser return truncated json
        # If CSV/JSON return full payload.
        serializer_class = QuerySerializerList
        if self.action == 'list':
            serializer_class = QuerySerializerList
        if self.action == 'retrieve':
            serializer_class = QuerySerializerRetrieve
        if self.action == 'create' or self.action == 'update':
            serializer_class = QuerySerializerCreateUpdate

        return serializer_class

    def get_queryset(self):
        """
        This view should return a list of all thqueriests
        for the currently authenticated user.

        """
        user = self.request.user
        return Query.objects.filter(owner=user).order_by('-updated')

    def truncated_api_response_data(self, accepted_media_type, serialized_valid_data):
        """
        If the response is text/html (browsable api) then truncate to render limit and send flag info

        """
        # Make a copy of the data (already know is_valid() in create method)
        new_serializer_data = serialized_valid_data

        if accepted_media_type == 'text/html':
            # Truncate response to browser but leave json and csv
            query_results_rows = len(serialized_valid_data['queryResults']['index'])
            query_results_cols = len(serialized_valid_data['queryResults']['columns'])
            render_limit = 10000
            # render_limit = 10

            if query_results_cols * query_results_rows >= render_limit:
                # Get new row limit
                new_query_results_rows = int(render_limit / query_results_cols)
                # Truncate results
                new_data = serialized_valid_data['queryResults']['data'][0:new_query_results_rows]
                new_index = serialized_valid_data['queryResults']['index'][0:new_query_results_rows]
                new_serializer_data['queryResults']['data'] = new_data
                new_serializer_data['queryResults']['index'] = new_index
                new_serializer_data['flag'] = {'query_results_rows': query_results_rows, 'render_limit': render_limit,
                                               'new_query_results_rows': new_query_results_rows}

        return new_serializer_data

    def retrieve(self, request, *args, **kwargs):
        """ Retrieve a model instance. """
        instance = self.get_object()
        serializer = self.get_serializer(instance)

        return Response(self.truncated_api_response_data(accepted_media_type=request.accepted_media_type,
                                                         serialized_valid_data=serializer.data))

    def run_fidia(self, request_string):

        # SELECT t1.CATAID FROM InputCatA AS t1 WHERE t1.CATAID  BETWEEN 65401 and 65410
        sample = AsvoSparkArchive().new_sample_from_query(request_string)

        # (json_n_rows, json_n_cols) = sample.tabular_data().shape
        # json_element_cap = 100000
        # json_row_cap = 2000

        json_table = sample.tabular_data().reset_index().to_json(orient='split')

        # Turned off capping data on the back end. The time issue is due to the
        # browser rendering on the front end using dataTables.js.
        # This view should still pass back *all* the data:
        # http: // 127.0.0.1:8000/asvo/data/query/32/?format=json

        # if (json_n_rows*json_n_cols < json_element_cap ):
        #     json_table = sample.tabular_data().reset_index().to_json(orient='split')
        #     json_flag = 0
        # else:
        #     # json_table = sample.tabular_data().reset_index().to_json(orient='split')
        #     json_table = sample.tabular_data().iloc[:json_row_cap].reset_index().to_json(orient='split')
        #     json_flag = json_row_cap

        log.debug(json_table)
        data = json.loads(json_table)

        return data

    def create(self, request, *args, **kwargs):
        """
        Create a model instance. Override CreateModelMixin create to catch the POST data for processing before save
        Return only the location of the new resource in data['url'] as per HTTP spec.
        """
        saved_object = request.data
        # Raise error if SQL field is empty
        if "SQL" in saved_object:
            if not saved_object["SQL"]:
                raise CustomValidation("SQL Field Blank", 'detail', 400)
            else:
                saved_object["queryResults"] = self.run_fidia(saved_object["SQL"])
                # serializer = self.get_serializer(data=request.data)
                serializer = self.get_serializer(data=saved_object)
                serializer.is_valid(raise_exception=True)
                self.perform_create(serializer)
                headers = self.get_success_headers(serializer.data)
                # return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
                location_only = serializer.data
                location_only.clear()
                location_only['url'] = serializer.data['url']
                location_only['title'] = serializer.data['title']
                location_only['created'] = serializer.data['created']

                return Response(location_only, status=status.HTTP_201_CREATED, headers=headers)
        else:
            raise CustomValidation("SQL Field Blank", 'detail', 400)

    def perform_create(self, serializer):
        """
        Override CreateModelMixin perform_create to save object instance with ownership
        """
        serializer.save(owner=self.request.user)

    def update(self, request, *args, **kwargs):
        """
        Update a model instance.
        """
        partial = kwargs.pop('partial', False)
        instance = self.get_object()

        # current SQL
        saved_object = instance
        # inbound request
        incoming_object = self.request.data

        # override the incoming queryResults with the saved version
        incoming_object['queryResults']=(saved_object.queryResults)

        # if new sql (and/or results have been tampered with), re-run fidia and override results
        # if (incoming_object['SQL'] != saved_object.SQL) or (testQueryResultsTamper.data['queryResults'] != saved_object.queryResults):
        if incoming_object['SQL'] != saved_object.SQL:
            # if (testQueryResultsTamper.data['queryResults'] != saved_object.queryResults):
            #     pprint('qR changed')
            #     raise PermissionDenied(detail="WARNING - editing the query result is forbidden. Editable fields: title, SQL.")
            incoming_object['queryResults'] = self.run_FIDIA(self.request.data)
            pprint('update object')

        serializer = self.get_serializer(instance, data=incoming_object, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)

    def perform_update(self, serializer):
        serializer.save()

    def partial_update(self, request, *args, **kwargs):
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def perform_destroy(self, instance):
        instance.delete()


class UserViewSet(viewsets.ReadOnlyModelViewSet):
    """
    This viewset automatically provides `list` and `detail` actions.
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAdminUser]


# from fidia.archive.example_archive import ExampleArchive
# ar = ExampleArchive()
# sample = ar.get_full_sample()

from fidia.archive.sami import SAMITeamArchive
# ar = SAMITeamArchive(
#     "/net/aaolxz/iscsi/data/SAMI/data_releases/v0.9/",
#     "/net/aaolxz/iscsi/data/SAMI/catalogues/" +
#     "sami_sel_20140911_v2.0JBupdate_July2015_incl_nonQCmet_galaxies.fits")

ar = SAMITeamArchive(
    settings.SAMI_TEAM_DATABASE,
    settings.SAMI_TEAM_DATABASE_CATALOG)

sample = ar.get_full_sample()

# >>> ar.schema()
# {'line_map': {'value': 'float.ndarray', 'variance': 'float.ndarray'},
# 'redshift': {'value': 'float'},
# 'spectral_map': {'extra_value': 'float',
#    'galaxy_name': 'string',
#    'value': 'float.array',
#    'variance': 'float.array'},
# 'velocity_map': {'value': 'float.ndarray', 'variance': 'float.ndarray'}}
#
# >>> sample['Gal1']['redshift'].value
# 3.14159
#
class GAMAViewSet(mixins.ListModelMixin,
                    viewsets.GenericViewSet):

    renderer_classes = (GAMARenderer, renderers.JSONRenderer, r.CSVRenderer)
    def list(self, request, pk=None, sample_pk=None, format=None):
        try:
            sample
        except KeyError:
            return Response(status=status.HTTP_404_NOT_FOUND)
        except ValueError:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        return Response({'nodata': True})


class samiViewSet(mixins.ListModelMixin,
                    viewsets.GenericViewSet):

    renderer_classes = (SampleRenderer, renderers.JSONRenderer, r.CSVRenderer)

    def list(self, request, pk=None, sample_pk=None, format=None):
        try:
            sample
        except KeyError:
            return Response(status=status.HTTP_404_NOT_FOUND)
        except ValueError:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        serializer_class = SampleSerializer
        serializer = serializer_class(
            instance=sample, many=False,
            context={'request': request},
            depth_limit=1
        )
        return Response(serializer.data)


class AstroObjectViewSet(mixins.ListModelMixin,
                    viewsets.GenericViewSet):

    # TODO ensure proper http status code is returned (page not found) on non-identifiable traits
    # TODO split the SOV html template into per-survey-type
    # TODO THIS SHOULD WORK: renderer_classes = (SOVRenderer, ) + api_settings.DEFAULT_RENDERER_CLASSES

    # renderer_classes = (GalaxySOVRenderer, renderers.JSONRenderer, r.CSVRenderer)
    renderer_classes = (AstroObjectRenderer, renderers.JSONRenderer, r.CSVRenderer)

    def list(self, request, pk=None, sample_pk=None, galaxy_pk=None, format=None):
        # def get_serializer_context(self):
        #     """
        #     pass request attribute to serializer - add schema attribute
        #     """
        #     return {
        #         'request': self.request,
        #         'schema': ar.schema()
        #     }

        try:
            astroobject = sample[galaxy_pk]
        except KeyError:
            return Response(status=status.HTTP_404_NOT_FOUND)
        except ValueError:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        serializer_class = AstroObjectSerializer

        sorted_schema = dict(collections.OrderedDict(ar.schema()))

        serializer = serializer_class(
            instance=astroobject, many=False,
            context={
                'request': request,
                'schema': sorted_schema
                }
        )

        return Response(serializer.data)


class TraitViewSet(mixins.ListModelMixin,
                    viewsets.GenericViewSet):

    renderer_classes = (TraitRenderer, renderers.JSONRenderer, r.CSVRenderer, FITSRenderer)

    def list(self, request, pk=None, sample_pk=None, galaxy_pk=None, trait_pk=None, format=None):
        log.debug("Format requested is '%s'", format)

        try:
            trait = sample[galaxy_pk][trait_pk]
        except KeyError:
            return Response(status=status.HTTP_404_NOT_FOUND)
        except ValueError:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        serializer_class = AstroObjectTraitSerializer
        serializer = serializer_class(
            instance=trait, many=False,
            context={
                'request': request,
            }
        )

        return Response(serializer.data)

    def finalize_response(self, request, response, *args, **kwargs):
        response = super().finalize_response(request, response, *args, **kwargs)
        if response.accepted_renderer.format == 'fits':
            filename = "{obj_id}-{trait}.fits".format(
                obj_id=kwargs['galaxy_pk'],
                trait=kwargs['trait_pk'])
            response['content-disposition'] = "attachment; filename=%s" % filename
        return response

class TraitPropertyViewSet(mixins.ListModelMixin,
                            viewsets.GenericViewSet):

    renderer_classes = (TraitPropertyRenderer, renderers.JSONRenderer, r.CSVRenderer)

    def list(self, request, pk=None, sample_pk=None, galaxy_pk=None, trait_pk=None, traitproperty_pk=None, format=None):
        try:
            # address trait properties via . not []
            trait_property = getattr(sample[galaxy_pk][trait_pk], traitproperty_pk)
        except KeyError:
            return Response(status=status.HTTP_404_NOT_FOUND)
        except ValueError:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        except AttributeError:
            raise NoPropertyFound("No property %s" % traitproperty_pk)
            # return Response(status=status.HTTP_404_NOT_FOUND)

        serializer_class = AstroObjectTraitPropertySerializer
        serializer = serializer_class(
            instance=trait_property, many=False,
            context={'request': request}
        )
        return Response(serializer.data)

    def finalize_response(self, request, response, *args, **kwargs):
        response = super().finalize_response(request, response, *args, **kwargs)
        if response.accepted_renderer.format == 'fits':
            filename = "{galaxy_pk}-{trait_pk}-{traitproperty_pk}.fits".format(**kwargs)
            response['content-disposition'] = "attachment; filename=%s" % filename
        return response


#  SOV
class SOVListSurveysViewSet(viewsets.ViewSet):

    renderer_classes = (SOVListRenderer, renderers.JSONRenderer, r.CSVRenderer)

    def list(self, request, pk=None, sample_pk=None, format=None):
        """
        List all available objects in fidia
         - this will have autocomplete form
        """
        try:
            sample
        except KeyError:
            return Response(status=status.HTTP_404_NOT_FOUND)
        except ValueError:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        serializer_class = SOVListSurveysSerializer
        serializer = serializer_class(
            instance=sample, many=True,
            context={'request': request},
        )
        return Response(serializer.data)


# Necessary to split the list and detail views so different
# renderer classes can be implemented (and therefore different html templates)


class SOVRetrieveObjectViewSet(mixins.RetrieveModelMixin,
                                viewsets.GenericViewSet):
    renderer_classes = (SOVDetailRenderer, renderers.JSONRenderer, r.CSVRenderer)

    def retrieve(self, request, pk=None, sample_pk=None, format=None):
        try:
            astroobject = sample[pk]
        except KeyError:
            return Response(status=status.HTTP_404_NOT_FOUND)
        except ValueError:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        serializer = SOVRetrieveObjectSerializer(
            instance=astroobject, many=False,
            context={'request': request}
        )
        return Response(serializer.data)


class AvailableTables(views.APIView):

    def get(self, request, format=None):
        """
        Return hardcoded response: json data of available tables
        """
        with open('restapi_app/gama_database.json') as json_d:
            json_data = json.load(json_d)
        return Response(json_data)


class ContactForm(views.APIView):
    """
    Contact Form
    """

    permission_classes = (permissions.AllowAny,)
    renderer_classes = [renderers.TemplateHTMLRenderer]
    template_name = 'restapi_app/support/contact.html'

    def get(self, request):

        serializer = ContactFormSerializer

        return Response({'serializer': serializer})

    def post(self, request, format=None):

        serializer = ContactFormSerializer(data=request.data)
        serializer.is_valid()

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_202_ACCEPTED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
