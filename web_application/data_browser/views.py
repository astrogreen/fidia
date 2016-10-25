from collections import OrderedDict
import random, collections, logging, json, requests, zipfile, io, itertools

import django.core.exceptions
from django.contrib.auth.models import User
from django.conf import settings
from django.http import HttpResponse, StreamingHttpResponse
from django.views.generic import View

from asvo.fidia_samples_archives import sami_dr1_sample, sami_dr1_archive as ar

from rest_framework import generics, permissions, renderers, mixins, views, viewsets, status, mixins, exceptions, \
    renderers
from rest_framework.response import Response
from rest_framework.settings import api_settings
from rest_framework.reverse import reverse

import restapi_app.permissions
import restapi_app.exceptions
import restapi_app.renderers
import restapi_app.utils.helpers

import data_browser.serializers
import data_browser.renderers
import data_browser.mixins
import data_browser.helpers

import fidia.exceptions
from fidia.traits import Trait, TraitProperty, TraitKey
from fidia import traits

import fidia_tarfile_helper

log = logging.getLogger(__name__)


def invert_dict(inverted_dict):
    elements = inverted_dict.iteritems()
    for flag_value, flag_names in elements:
        for flag_name in flag_names:
            yield flag_name, flag_value

class RootViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    """ Viewset for DataBrowser API root. Implements List action only.
    Lists all surveys, their current versions and total number of objects in that version. """

    renderer_classes = (data_browser.renderers.RootRenderer, renderers.JSONRenderer)
    permission_classes = [permissions.AllowAny]

    def list(self, request, pk=None, format=None):
        # Request available samples from FIDIA
        surveys = [
            {"survey": "sami", "count": sami_dr1_sample.ids.__len__(), "current_version": 1.0},
            {"survey": "gama", "count": 0, "current_version": 0},
            {"survey": "galah", "count": 0, "current_version": 0}
        ]

        self.breadcrumb_list = ['Data Browser']

        serializer_class = data_browser.serializers.RootSerializer
        serializer = serializer_class(
            many=False, instance=sami_dr1_sample,
            context={'request': request, 'surveys': surveys},
        )
        return Response(serializer.data)


class SurveyViewSet(mixins.ListModelMixin, viewsets.GenericViewSet, mixins.CreateModelMixin):
    """
    Viewset for Sample route. Provides List view AND create (post) to download data.
    Endpoint: list of astroobjects
    HTML Context: survey string ('sami') and survey catalogue data
    """

    renderer_classes = (data_browser.renderers.SurveyRenderer, renderers.JSONRenderer)
    permission_classes = [permissions.AllowAny]
    serializer_class = data_browser.serializers.DownloadSerializer

    def __init__(self, *args, **kwargs):
        self.catalog = ''

    def list(self, request, pk=None, survey_pk=None, format=None, extra_keyword=None):

        self.breadcrumb_list = ['Data Browser', str(survey_pk).upper()]

        try:
            # TODO ask FIDIA what it's got for survey_pk
            sami_dr1_sample
            if survey_pk != "sami":
                message = 'Survey does not exist: ' + survey_pk
                raise restapi_app.exceptions.CustomValidation(detail=message, field='detail',
                                                                  status_code=status.HTTP_404_NOT_FOUND)
        except KeyError:
            return Response(status=status.HTTP_404_NOT_FOUND)
        except ValueError:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        # Context (for html page render)
        self.catalog = json.dumps(sami_dr1_sample.get_feature_catalog_data())

        # Endpoint-only
        serializer_class = data_browser.serializers.SurveySerializer
        serializer = serializer_class(
            instance=sami_dr1_sample, many=False,
            context={'request': request, 'survey': survey_pk}
        )
        return Response(serializer.data)

    def create(self, request, pk=None, survey_pk=None, *args, **kwargs):

        download_data = json.loads(request.POST['download'])

        object_list = (download_data['objects']).split(',')
        product_list = json.loads(download_data['products'])

        # product_list will look like the following:
        #
        #    {
        #        "SAMI": [
        #            {
        #                "trait_key": "velocity_map-ionized_gas-recom_comp-V02",
        #                "trait_key_arr": [
        #                    "velocity_map",
        #                    "ionized_gas",
        #                    "recom_comp",
        #                    "V02"
        #                ]
        #            },
        #            {
        #                "trait_key": "extinction_map--recom_comp-V02",
        #                "trait_key_arr": [
        #                    "extinction_map",
        #                    "null",
        #                    "recom_comp",
        #                    "V02"
        #                ]
        #            }
        #        ]
        #    }

        trait_path_list = []
        for obj, product in itertools.product(object_list, product_list['SAMI']):

            trait_key_array = product['trait_key_arr'] # type: list
            # Convert "null" to (Python) None in the list
            while "null" in trait_key_array:
                trait_key_array[trait_key_array.index("null")] = None

            trait_path = {
                'survey': 'SAMI',
                'object_id': obj,
                'trait_path': [TraitKey(*trait_key_array)]
            }

            trait_path_list.append(trait_path)

        tar_stream = fidia_tarfile_helper.fidia_tar_file_generator(sami_dr1_sample, trait_path_list)

        response = StreamingHttpResponse(tar_stream, content_type='application/gzip')
        filename = 'SAMI_data.tar.gz'
        response['content-disposition'] = "attachment; filename=%s" % filename

        return response

# class Download(views.APIView):
#     def get(self, request, *args, **kwargs):
#         """Example code to prove it works"""
#
#         # @TODO: Delete/udpate this function!
#
#         trait_path_list = [
#             {'survey': 'SAMI',
#              'object_id': '9352',
#              'trait_path': [
#                  "velocity_map-ionized_gas"
#              ]},
#             {'survey': 'SAMI',
#              'object_id': '9352',
#              'trait_path': [
#                  "velocity_dispersion_map-ionized_gas"
#              ]}
#             # {'survey': 'SAMI',
#             #  'object_id': '24433',
#             #  'trait_path': [
#             #      "spectral_cube-blue"
#             #  ]}
#         ]
#
#         tar_stream = fidia_tarfile_helper.fidia_tar_file_generator(sami_dr1_sample, trait_path_list)
#
#         return StreamingHttpResponse(tar_stream, content_type='application/gzip')
#
#     def post(self, request, *args, **kwargs):
#
#         object_list = (request.POST['objects']).split(',')
#         product_list = json.loads(request.POST['products'])
#
#         # product_list will look like the following:
#         #
#         #    {
#         #        "SAMI": [
#         #            {
#         #                "trait_key": "velocity_map-ionized_gas-recom_comp-V02",
#         #                "trait_key_arr": [
#         #                    "velocity_map",
#         #                    "ionized_gas",
#         #                    "recom_comp",
#         #                    "V02"
#         #                ]
#         #            },
#         #            {
#         #                "trait_key": "extinction_map--recom_comp-V02",
#         #                "trait_key_arr": [
#         #                    "extinction_map",
#         #                    "null",
#         #                    "recom_comp",
#         #                    "V02"
#         #                ]
#         #            }
#         #        ]
#         #    }
#
#         trait_path_list = []
#         for obj, product in itertools.product(object_list, product_list['SAMI']):
#
#             trait_key_array = product['trait_key_arr'] # type: list
#             # Convert "null" to (Python) None in the list
#             while "null" in trait_key_array:
#                 trait_key_array[trait_key_array.index("null")] = None
#
#             trait_path = {
#                 'survey': 'SAMI',
#                 'object_id': obj,
#                 'trait_path': [TraitKey(*trait_key_array)]
#             }
#
#             trait_path_list.append(trait_path)
#
#         tar_stream = fidia_tarfile_helper.fidia_tar_file_generator(sami_dr1_sample, trait_path_list)
#
#         return StreamingHttpResponse(tar_stream, content_type='application/gzip')


class AstroObjectViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    """ Viewset for Astroobject. Provides List view only.
    Endpoint: available traits (plus branches/versions)
    HTML context: survey string, astroobject, traits and position (ra,dec)"""

    def __init__(self, *args, **kwargs):
        self.survey = self.astro_object = self.feature_catalog_data = ''
        # super().__init__()

    renderer_classes = (data_browser.renderers.AstroObjectRenderer, renderers.JSONRenderer)
    permission_classes = [permissions.AllowAny]

    def list(self, request, pk=None, survey_pk=None, astroobject_pk=None, format=None):

        self.breadcrumb_list = ['Data Browser', str(survey_pk).upper(), astroobject_pk]

        try:
            astro_object = sami_dr1_sample[astroobject_pk]
            assert isinstance(astro_object, fidia.AstronomicalObject)
        except fidia.exceptions.NotInSample:
            message = 'Object ' + astroobject_pk + ' Not Found'
            raise restapi_app.exceptions.CustomValidation(detail=message, field='detail',
                                                          status_code=status.HTTP_404_NOT_FOUND)
        except KeyError:
            return Response(data={}, status=status.HTTP_404_NOT_FOUND)
        except ValueError:
            return Response(data={}, status=status.HTTP_400_BAD_REQUEST)

        if survey_pk != "sami":
            message = 'Survey does not exist: ' + survey_pk
            raise restapi_app.exceptions.CustomValidation(detail=message, field='detail',
                                                          status_code=status.HTTP_404_NOT_FOUND)
        # Context (for html page render)
        self.survey = survey_pk
        self.astro_object = astroobject_pk
        self.feature_catalog_data = astro_object.get_feature_catalog_data()

        # Endpoint-only
        serializer_class = data_browser.serializers.AstroObjectSerializer
        serializer = serializer_class(
            instance=astro_object, many=False,
            context={
                'survey': survey_pk,
                'astro_object': astroobject_pk,
                'request': request,
                'traits': ar.full_schema(include_subtraits=False, data_class='all', combine_levels=None,
                                 verbosity='descriptions', separate_metadata=True),
                'position': {'ra': astro_object.ra, 'dec': astro_object.dec}
            }
        )
        return Response(serializer.data)


class TraitViewSet(mixins.ListModelMixin, viewsets.GenericViewSet, data_browser.helpers.TraitHelper):
    """ Viewset for Trait. Provides List view only.
    Endpoint: available properties
    HTML context: survey string, astroobject, all available branches"""

    def __init__(self, *args, **kwargs):

        # call init method from TraitHelper (superclass)
        self.breadcrumb_list = []
        data_browser.helpers.TraitHelper.__init__(self)
        # super().__init__()

    permission_classes = [permissions.AllowAny]
    renderer_classes = (data_browser.renderers.TraitRenderer, renderers.JSONRenderer, data_browser.renderers.FITSRenderer)

    def list(self, request, pk=None, survey_pk=None, astroobject_pk=None, trait_pk=None, format=None):

        try:
            trait = sami_dr1_sample[astroobject_pk][trait_pk]
            self.breadcrumb_list = ['Data Browser', str(survey_pk).upper(), astroobject_pk, trait.get_pretty_name()]
        except fidia.exceptions.NotInSample:
            message = 'Object ' + astroobject_pk + ' Not Found'
            raise restapi_app.exceptions.CustomValidation(detail=message, field='detail',
                                                          status_code=status.HTTP_404_NOT_FOUND)
        except fidia.exceptions.UnknownTrait:
            message = 'Not found: Object ' + astroobject_pk + ' does not have property ' + trait_pk
            raise restapi_app.exceptions.CustomValidation(detail=message, field='detail',
                                                          status_code=status.HTTP_404_NOT_FOUND)
        except KeyError:
            message = 'Key Error: ' + trait_pk + ' does not exist'
            raise restapi_app.exceptions.CustomValidation(detail=message, field='detail',
                                                          status_code=status.HTTP_404_NOT_FOUND)
        except ValueError:
            message = 'Value Error: ' + trait_pk + ' does not exist'
            raise restapi_app.exceptions.CustomValidation(detail=message, field='detail',
                                                          status_code=status.HTTP_404_NOT_FOUND)

        # Context (for html page render)
        self.set_attributes(survey_pk=survey_pk, astroobject_pk=astroobject_pk, trait_pk=trait_pk,
                            trait=trait, ar=ar)
        self.fidia_type = "trait"

        if isinstance(trait, traits.Map2D):
            self.trait_2D_map = True

        # Endpoint
        serializer_class = data_browser.serializers.TraitSerializer
        serializer = serializer_class(
            instance=trait, many=False,
            context={
                'request': request,
                'trait_url': self.trait_url,
            }
        )

        return Response(serializer.data)

    def finalize_response(self, request, response, *args, **kwargs):
        response = super().finalize_response(request, response, *args, **kwargs)
        if response.accepted_renderer.format == 'fits':
            filename = "{obj_id}-{trait}.fits".format(
                obj_id=kwargs['astroobject_pk'],
                trait=kwargs['trait_pk'])
            response['content-disposition'] = "attachment; filename=%s" % filename
        return response


class SubTraitPropertyViewSet(mixins.ListModelMixin, viewsets.GenericViewSet, data_browser.helpers.TraitHelper):
    """
    Dynamic View evaluated on instance type is Trait or Trait property
    This is only one level
    """
    renderer_classes = (data_browser.renderers.SubTraitPropertyRenderer, renderers.JSONRenderer)
    permission_classes = [permissions.AllowAny]

    def __init__(self, *args, **kwargs):
        # call init method from TraitHelper (superclass)
        self.template = 'data_browser/trait_property/list.html'
        data_browser.helpers.TraitHelper.__init__(self)

    def list(self, request, survey_pk=None, astroobject_pk=None, trait_pk=None, subtraitproperty_pk=None, format=None):

        try:
            # Determine what we're looking at.
            # type_for_trait_path requires the trait_key and current "path"
            path = [subtraitproperty_pk]  # < class 'list'>: ['value']
            path.insert(0, trait_pk)  # < class 'list'>: ['line_emission_map-HBETA', 'value']

        except:
            message = 'Not found: Object ' + astroobject_pk + ' trait ' + trait_pk + ' does not have property ' + subtraitproperty_pk
            raise restapi_app.exceptions.CustomValidation(detail=message, field='detail',
                                                          status_code=status.HTTP_404_NOT_FOUND)

        # Context (for html page render)
        try:
            trait_pointer = sami_dr1_sample[astroobject_pk][trait_pk]
        except KeyError:
            _branch = trait_pk.split(":")[1]
            message = 'No ' + trait_pk + ' data available for ' + astroobject_pk +'. Check the branch and version ['+_branch+'] are correct.'
            raise restapi_app.exceptions.CustomValidation(detail=message, field='detail',
                                                          status_code=status.HTTP_404_NOT_FOUND)
        except fidia.exceptions.UnknownTrait:
            message = 'Unknown trait: ' + trait_pk
            raise restapi_app.exceptions.CustomValidation(detail=message, field='detail',
                                                          status_code=status.HTTP_404_NOT_FOUND)

        self.set_attributes(survey_pk=survey_pk, astroobject_pk=astroobject_pk, trait_pk=trait_pk,
                            trait=trait_pointer, ar=ar)

        if issubclass(ar.type_for_trait_path(path), Trait):
            self.template = 'data_browser/sub_trait/list.html'
            self.fidia_type = "sub_trait"
            subtrait_pointer = trait_pointer[subtraitproperty_pk]

            serializer = data_browser.serializers.TraitSerializer(
                instance=subtrait_pointer, many=False,
                context={'request': request,
                         'trait_url': reverse("data_browser:trait-list",
                                              kwargs={'survey_pk': survey_pk, 'astroobject_pk': astroobject_pk,
                                                      'trait_pk': trait_pk, }),
                         })
            # Set Breadcrumbs for this method
            self.breadcrumb_list = ['Data Browser', str(survey_pk).upper(), astroobject_pk,
                                    trait_pointer.get_pretty_name(),
                                    subtrait_pointer.get_pretty_name()]


        elif issubclass(ar.type_for_trait_path(path), TraitProperty):

            try:
                traitproperty_pointer = getattr(trait_pointer, subtraitproperty_pk)
            except:
                message = 'Not found: Object ' + astroobject_pk + ' trait ' + trait_pk + ' does not have property ' + subtraitproperty_pk
                raise restapi_app.exceptions.CustomValidation(detail=message, field='detail',
                                                              status_code=status.HTTP_404_NOT_FOUND)

            self.template = 'data_browser/trait_property/list.html'
            self.fidia_type = "trait_property"

            # Set Breadcrumbs for this method
            self.breadcrumb_list = ['Data Browser', str(survey_pk).upper(), astroobject_pk,
                                    trait_pointer.get_pretty_name(),
                                    traitproperty_pointer.get_pretty_name()]

            if 'array' in traitproperty_pointer.type and 'string' not in traitproperty_pointer.type:
                try:
                    n_axes = len(traitproperty_pointer.value.shape)
                except AttributeError:
                    pass
                except fidia.exceptions.DataNotAvailable:
                    message = 'No '+subtraitproperty_pk+' data available for ' + trait_pk
                    raise restapi_app.exceptions.CustomValidation(detail=message, field='detail',
                                                                  status_code=status.HTTP_404_NOT_FOUND)
                else:
                    if n_axes == 2:
                        self.trait_2D_map = True
                        # @TODO: Handle arrays other than numpy ndarrays

            serializer = data_browser.serializers.TraitPropertySerializer(
                instance=traitproperty_pointer, many=False,
                context={'request': request,
                         'trait_url': reverse("data_browser:trait-list",
                                              kwargs={'survey_pk': survey_pk, 'astroobject_pk': astroobject_pk,
                                                      'trait_pk': trait_pk, }),
                         })

        else:
            raise Exception("An error has occurred.")

        return Response(serializer.data)


class TraitPropertyViewSet(mixins.ListModelMixin, viewsets.GenericViewSet, data_browser.helpers.TraitHelper):
    """
    Final level of nesting - this will provide a level to all those sub-trait/traitproperty views.
    Might not even need it - may be able to pass through SubTraitProperty Viewset with carefully managed pks
    """
    permission_classes = [permissions.AllowAny]
    renderer_classes = (data_browser.renderers.SubTraitPropertyRenderer, renderers.JSONRenderer)

    def __init__(self, survey=None, astro_object=None, trait=None, template=None, *args, **kwargs):
        self.template = 'data_browser/trait_property/list.html'
        data_browser.helpers.TraitHelper.__init__(self)

    def list(self, request, survey_pk=None, astroobject_pk=None, trait_pk=None, subtraitproperty_pk=None,
             traitproperty_pk=None, format=None):

        self.breadcrumb_list = ['Data Browser', str(survey_pk).upper(), astroobject_pk, trait_pk,
                                subtraitproperty_pk, traitproperty_pk]

        # set trait attributes on the renderer context
        try:
            trait_pointer = sami_dr1_sample[astroobject_pk][trait_pk]
        except KeyError:
            message = "Key not found: " + trait_pk
            raise restapi_app.exceptions.CustomValidation(detail=message, field='detail',
                                                          status_code=status.HTTP_404_NOT_FOUND)
        try:
            subtrait_pointer = sami_dr1_sample[astroobject_pk][trait_pk][subtraitproperty_pk]
        except KeyError:
            message = "Key not found: " + subtraitproperty_pk
            raise restapi_app.exceptions.CustomValidation(detail=message, field='detail',
                                                      status_code=status.HTTP_404_NOT_FOUND)
        try:
            traitproperty_pointer = getattr(sami_dr1_sample[astroobject_pk][trait_pk][subtraitproperty_pk],
                                            traitproperty_pk)
        except Exception:
            message = "Key not found: " + traitproperty_pk
            raise restapi_app.exceptions.CustomValidation(detail=message, field='detail',
                                                          status_code=status.HTTP_404_NOT_FOUND)

        # Context (for html page render)
        self.set_attributes(survey_pk=survey_pk, astroobject_pk=astroobject_pk, trait_pk=trait_pk,
                            trait=trait_pointer, ar=ar)

        self.fidia_type = "trait_property"
        self.subtrait_pretty_name = subtrait_pointer.get_pretty_name()

        self.trait_2D_map = False
        if isinstance(self.trait, traits.Map2D):
            self.trait_2D_map = True

        serializer = data_browser.serializers.TraitPropertySerializer(
            instance=traitproperty_pointer, many=False,
            context={'request': request,
                     'trait_url': reverse("data_browser:trait-list",
                                          kwargs={'survey_pk': survey_pk, 'astroobject_pk': astroobject_pk,
                                                  'trait_pk': trait_pk, }),
                     }
        )

        self.breadcrumb_list = ['Data Browser', str(survey_pk).upper(), astroobject_pk, trait_pointer.get_pretty_name(),
                                subtrait_pointer.get_pretty_name(), traitproperty_pointer.get_pretty_name()]

        return Response(serializer.data)
