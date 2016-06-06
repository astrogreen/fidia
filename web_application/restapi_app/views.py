import random, collections, logging
import json
from pprint import pprint
from .permissions import IsNotAuthenticated
import restapi_app.exceptions

from .serializers import (
    CreateUserSerializer,
    UserSerializer,
    ContactFormSerializer,
    SampleSerializer,
    AstroObjectSerializer,
    AstroObjectTraitSerializer,
    AstroObjectTraitPropertySerializer,
    SOVListSurveysSerializer,
)

import restapi_app.renderers
import restapi_app.serializers

from .renderers import (
    FITSRenderer,
    SOVListRenderer,
    SOVDetailRenderer,
    AstroObjectRenderer,
    GAMARenderer,
    SampleRenderer,
    TraitRenderer,
    TraitPropertyRenderer
)

from rest_framework import generics, permissions, renderers, mixins, views, viewsets, status, mixins, exceptions
from rest_framework.response import Response
from django.contrib.auth.models import User

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
    renderer_classes = [restapi_app.renderers.CreateUserRenderer, renderers.JSONRenderer]

    def get_queryset(self):
        queryset = User.objects.none()
        return queryset


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

    renderer_classes = (GAMARenderer, renderers.JSONRenderer)
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

    renderer_classes = (SampleRenderer, renderers.JSONRenderer)

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


    renderer_classes = (AstroObjectRenderer, renderers.JSONRenderer)

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
    """
    The Trait View
    """

    renderer_classes = (TraitRenderer, renderers.JSONRenderer, FITSRenderer)

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

    renderer_classes = (TraitPropertyRenderer, renderers.JSONRenderer)

    def list(self, request, pk=None, sample_pk=None, galaxy_pk=None, trait_pk=None, traitproperty_pk=None, format=None):
        try:
            # address trait properties via . not []
            trait_property = getattr(sample[galaxy_pk][trait_pk], traitproperty_pk)
        except KeyError:
            return Response(status=status.HTTP_404_NOT_FOUND)
        except ValueError:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        except AttributeError:
            raise restapi_app.exceptions.NoPropertyFound("No property %s" % traitproperty_pk)
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


class TestingViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):

    def list(self, request, pk=None, dynamic_pk=None, dynamic_pk0=None, format=None):
        # @property
        # def dynamic_property_first_of_type(self, dynamic_pk):
            # split on /
        print(dynamic_pk.split('/'))
        dynamic_components = dynamic_pk.split('/')
        # first component distinction: ST/TP
        print(dynamic_components)
        print(type(dynamic_components))
        print(dynamic_components[:-1])

            # return 'test'

        return Response({'dynamic_pk': dynamic_pk, 'dy1=n1': dynamic_pk0})



# class DynamicPropertyViewSet(mixins.ListModelMixin,
#                             viewsets.GenericViewSet):
#     """
#     Differentiate between Trait and Sub-trait.
#     Allows for n levels of nesting - parses str
#     """
#     # @property
#     # def rendererclasses(self, level):
#     #     if level == "sub_trait":
#     #         return [restapi_app.renderers.SubTraitRenderer, renderers.JSONRenderer]
#     #     elif level == "trait_property":
#     #         return [restapi_app.renderers.TraitPropertyRenderer, renderers.JSONRenderer]
#     queryset = Qu
#
#     def list(self, request, pk=None, sample_pk=None, galaxy_pk=None, trait_pk=None, dynamic_pk=None, format=None):
#         # HERE FUNCTION TO DETERMINE TRAIT OR SUB-TRAIT
#         @property
#         def dynamic_property_first_of_type(self, dynamic_pk):
#             # split on /
#             print(dynamic_pk.split('/'))
#             dynamic_components = dynamic_pk.split('/')
#             # first component distinction: ST/TP
#             print(dynamic_components)
#             print(type(dynamic_components))
#             print(dynamic_components[:-1])
#
#             return 'test'
#
#         return Response()
    #
    #     try:
    #         dynamic_property = getattr(sample[galaxy_pk][trait_pk], dynamic_pk)
    #     except KeyError:
    #         return Response(status=status.HTTP_404_NOT_FOUND)
    #     except ValueError:
    #         return Response(status=status.HTTP_400_BAD_REQUEST)
    #     except AttributeError:
    #         raise NoPropertyFound("No property %s" % dynamic_pk)
    #
    #     @property
    #     def serializer_class(self, level, type):
    #         # some logic here to pick a serializer based on the level (trait/subtrait) and perhaps the type
    #         # (needs mapping)
    #         return AstroObjectTraitPropertySerializer
    #
    #     serializer = serializer_class(
    #         instance=dynamic_property, many=False,
    #         context={'request': request}
    #     )
    #     return Response(serializer.data)
    #
    # def finalize_response(self, request, response, *args, **kwargs):
    #     # TODO this needs changing based on ST/TP
    #     response = super().finalize_response(request, response, *args, **kwargs)
    #     if response.accepted_renderer.format == 'fits':
    #         filename = "{galaxy_pk}-{trait_pk}-{traitproperty_pk}.fits".format(**kwargs)
    #         response['content-disposition'] = "attachment; filename=%s" % filename
    #     return response


#  SOV
# class SOVListSurveysViewSet(viewsets.ViewSet):
#
#     renderer_classes = (SOVListRenderer, renderers.JSONRenderer)
#
#     def list(self, request, pk=None, sample_pk=None, format=None):
#         """
#         List all available objects in fidia
#          - this will have autocomplete form
#         """
#         try:
#             sample
#         except KeyError:
#             return Response(status=status.HTTP_404_NOT_FOUND)
#         except ValueError:
#             return Response(status=status.HTTP_400_BAD_REQUEST)
#
#         serializer_class = SOVListSurveysSerializer
#         serializer = serializer_class(
#             instance=sample, many=True,
#             context={'request': request},
#         )
#         return Response(serializer.data)
#
#
# # Necessary to split the list and detail views so different
# # renderer classes can be implemented (and therefore different html templates)
#
# class SOVRetrieveObjectViewSet(mixins.RetrieveModelMixin,
#                                    viewsets.GenericViewSet):
#     """
#     SOV retrieve single object.
#     Responds with only the schema, the available traits for this AO, and
#      the url of each trait. Will make AJAX calls for trait data.
#
#     """
#     renderer_classes = (SOVDetailRenderer, renderers.JSONRenderer)
#
#     def retrieve(self, request, pk=None, sample_pk=None, format=None):
#
#         try:
#             astroobject = sample[pk]
#         except KeyError:
#             return Response(status=status.HTTP_404_NOT_FOUND)
#         except ValueError:
#             return Response(status=status.HTTP_400_BAD_REQUEST)
#
#         serializer_class = restapi_app.serializers.SOVRetrieveSerializer
#
#         sorted_schema = dict(collections.OrderedDict(ar.schema()))
#
#         serializer = serializer_class(
#             instance=astroobject, many=False,
#             context={
#                 'request': request,
#                 'schema': sorted_schema,
#                 # 'key_info': key_info
#             }
#         )
#
#         return Response(serializer.data)


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
