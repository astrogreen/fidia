import random, collections
from pprint import pprint
from .exceptions import NoPropertyFound
from django.shortcuts import get_object_or_404

from .models import (
    Query,
)
from .serializers import (
    UserSerializer,
    QuerySerializerCreateUpdate, QuerySerializerList,
    SampleSerializer,
    AstroObjectSerializer,
    AstroObjectTraitSerializer,
    AstroObjectTraitPropertySerializer,
    SOVListSurveysSerializer,
    SOVRetrieveObjectSerializer
)

from .renderers import (
    FITSRenderer,
    ListNoDetailRenderer,
    SOVListRenderer,
    SOVDetailRenderer,
    QueryRenderer,
    AstroObjectRenderer,
    SampleRenderer
)

from rest_framework import generics, permissions, renderers, views, viewsets, status, mixins
from rest_framework.response import Response
from django.contrib.auth.models import User
from rest_framework_csv import renderers as r



class QueryViewSet(viewsets.ModelViewSet):
    serializer_class = QuerySerializerList
    permission_classes = [permissions.IsAuthenticated]
    # permission_classes = [permissions.AllowAny]
    #  permission_classes = (permissions.IsAuthenticatedOrReadOnly,
    #                       IsOwnerOrReadOnly,)
    queryset = Query.objects.all()
    renderer_classes = [QueryRenderer, renderers.JSONRenderer, r.CSVRenderer]

  # base_name = 'query'

    def get_serializer_class(self):
        serializer_class = QuerySerializerList

        if self.request.method == 'GET':
            serializer_class = QuerySerializerList
        elif (self.request.method == 'POST') or (self.request.method == 'PUT'):
            serializer_class = QuerySerializerCreateUpdate

        return serializer_class

    def get_queryset(self):
        """
        This view should return a list of all thqueriests
        for the currently authenticated user.
        """
        user = self.request.user
        return Query.objects.filter(owner=user).order_by('-updated')

    def run_FIDIA(self, request, *args, **kwargs):
        # TODO ADD FIDIA(request.data['SQL'])
        dummyData = {"columns":["cataid","z","metal"],
               # "index":  [random.randint(1,5),1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20],
               "data":   [[8823,0.0499100015,0.0163168724],
                          [63147,0.0499799997,0.0380015143],
                          [91963,0.0499899983,0.0106879927]]}
        for i in range(5):
            dummyData['data'].append([random.randint(1,5),random.randint(1,5),random.randint(1,5)])

        return dict(dummyData)

    def create(self, request, *args, **kwargs):
        """
        Create a model instance. Override CreateModelMixin create to catch the POST data for processing before save
        """
        # Overwrite the post request data (don't forget to set mutable!!)
        saved_object = request.POST
        saved_object._mutable = True
        saved_object['queryResults'] = self.run_FIDIA(request.data)
        serializer = self.get_serializer(data=saved_object)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

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

        #current SQL
        saved_object = instance
        #inbound request
        incoming_object = self.request.data
        # pprint('- - - - NEW PUT - - - -')
        # print(json.loads(incoming_object['queryResults']))
        # pprint('- - - - end PUT - - - -')
        # testQueryResultsTamper=self.get_serializer(instance, data=incoming_object, partial=True)
        # testQueryResultsTamper.is_valid(raise_exception=True)
        #
        # pprint(testQueryResultsTamper.data['queryResults'])
        # pprint(saved_object.queryResults)

        #override the incoming queryResults with the saved version
        incoming_object['queryResults']=(saved_object.queryResults)

        # if new sql (and/or results have been tampered with), re-run fidia and override results
        # if (incoming_object['SQL'] != saved_object.SQL) or (testQueryResultsTamper.data['queryResults'] != saved_object.queryResults):
        if incoming_object['SQL'] != saved_object.SQL:
            pprint('sql or qR changed')

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

# ASVO

# from fidia.archive.example_archive import ExampleArchive
# ar = ExampleArchive()
# sample = ar.get_full_sample()

from fidia.archive.sami import SAMITeamArchive
# ar = SAMITeamArchive(
#     "/net/aaolxz/iscsi/data/SAMI/data_releases/v0.9/",
#     "/net/aaolxz/iscsi/data/SAMI/catalogues/" +
#     "sami_sel_20140911_v2.0JBupdate_July2015_incl_nonQCmet_galaxies.fits")

ar = SAMITeamArchive(
    # "/home/agreen/sami_test_release/",
    "/Users/lmannering/Dropbox/AAO/SAMI/sami_test_release",
    # "/net/aaolxz/iscsi/data/SAMI/data_releases/v0.9/",
    # "/home/agreen/sami_test_release/sami_small_test_cat.fits")
    "/Users/lmannering/Dropbox/AAO/SAMI/sami_test_release/sami_small_test_cat.fits")
    # "/net/aaolxz/iscsi/data/SAMI/catalogues/" +
    # "sami_sel_20140911_v2.0JBupdate_July2015_incl_nonQCmet_galaxies.fits")
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


class SampleViewSet(mixins.ListModelMixin,
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
        def get_serializer_context(self):
            """
            pass request attribute to serializer - add schema attribute
            """
            return {
                'request': self.request,
                'schema': ar.schema()
            }

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

    renderer_classes = (ListNoDetailRenderer,renderers.JSONRenderer, r.CSVRenderer)

    def list(self, request, pk=None, sample_pk=None, galaxy_pk=None, trait_pk=None, format=None):
        try:
            trait = sample[galaxy_pk][trait_pk]
        except KeyError:
            return Response(status=status.HTTP_404_NOT_FOUND)
        except ValueError:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        serializer_class = AstroObjectTraitSerializer
        serializer = serializer_class(
            instance=trait, many=False,
            context={'request': request}
        )
        return Response(serializer.data)


class TraitPropertyViewSet(mixins.ListModelMixin,
                            viewsets.GenericViewSet):

    renderer_classes = (ListNoDetailRenderer,renderers.JSONRenderer, r.CSVRenderer)

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
        serializer_class = SOVRetrieveObjectSerializer
        serializer = serializer_class(
            instance=astroobject, many=False,
            context={'request': request}
        )
        return Response(serializer.data)