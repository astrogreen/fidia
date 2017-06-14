from rest_framework.decorators import detail_route, list_route
from rest_framework import generics, permissions, renderers, mixins, views, viewsets, status, mixins, exceptions, renderers
from rest_framework.response import Response

from collections import OrderedDict
import random, collections, logging, json, requests, zipfile, io, itertools
import xml.etree.ElementTree as ET

import django.core.exceptions
from django.contrib.auth.models import User
from django.conf import settings
from django.http import HttpResponse, StreamingHttpResponse
from django.views.generic import View

# from asvo.fidia_samples_archives import sami_dr1_sample, sami_dr1_archive as ar

from rest_framework.settings import api_settings
from rest_framework.reverse import reverse

import restapi_app.permissions
import restapi_app.exceptions
import restapi_app.renderers
import restapi_app.utils.helpers

import sov.serializers
# import sov.renderers
# import sov.mixins
# import sov.helpers

from sov.helpers.dummy_data.astro_object import ARCHIVE
from sov.helpers.dummy_data.survey import SURVEYS

# from fidia.traits.generic_traits import __all__ as available_traits
import fidia.traits.generic_traits
# import fidia.exceptions
# from fidia.traits import Trait, TraitProperty, TraitKey
# from fidia import traits

# import fidia_tarfile_helper

log = logging.getLogger(__name__)


def get_archive():
    return ARCHIVE


class Survey(viewsets.ReadOnlyModelViewSet):
    """
    Read-only access to the DC archive list of surveys.

    **Actions**
     list:
     Return a list of available surveys hosted by the DC archive.

     retrieve:
     Return the given astronomical object   
    """
    serializer_class = sov.serializers.SurveyList
    queryset = SURVEYS.values()

    def list(self, request, *args, **kwargs):
        queryset = list(SURVEYS.values())

        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def retrieve(self, request, pk=None, *args, **kwargs):
        instance = SURVEYS.get(pk)
        serializer = sov.serializers.SurveyRetrieve(instance=instance, many=False)
        return Response(serializer.data)


class AstroObject(viewsets.ReadOnlyModelViewSet):
    """
    Read-only access to the DC archive list of astronomical objects.
    
    **Actions**
     list:
     Return a list of available astronomic objects in the DC archive.
     
     retrieve:
     Return the given astronomical object   
    """
    serializer_class = sov.serializers.AstroObjectList
    queryset = get_archive().values()

    def list(self, request, *args, **kwargs):
        """
        List archive
        """
        queryset = list(ARCHIVE.values())
        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def retrieve(self, request, pk=None, *args, **kwargs):
        """
        Retrieve a AstroObject instance.
        """
        # Note, ARCHIVE[pk] will except if obj does not exist, .get(pk) returns None
        instance = ARCHIVE.get(pk)
        serializer = sov.serializers.AstroObjectRetrieve(instance=instance, many=False)
        return Response(serializer.data)


DATAFOR_DOC_STRING = (r"""
    Return data from FIDIA by type:

    keyword [trait, trait_property]:
""")


class DataFor(views.APIView):
    # Root view for filter-by, returns available urls for various types of filter
    # (keyword or position)
    def get(self, request, *args, **kwargs):
        return Response({
            'fidia_types': [
                {'type': 'trait', 'url': reverse('sov:data-for', kwargs={"fidia_type": "trait"}, request=request)},
                {'type': 'trait_property', 'url': reverse('sov:data-for', kwargs={"fidia_type": "trait_property"}, request=request)},
            ]
        })

DataFor.__doc__ = DATAFOR_DOC_STRING


class DataForType(generics.CreateAPIView):
    # Filter by a keyword or position
    queryset = get_archive().values()
    available_keywords = ['trait', 'trait_property']

    serializer_action_classes = {
        'trait': sov.serializers.DataForTrait,
        'trait_property': sov.serializers.DataForTraitProperty,
    }

    filter_serializer_classes = {
        'trait': sov.serializers.AOByTrait,
        'trait_property': sov.serializers.TraitByTraitProperty,
    }

    def get_serializer_class(self):
        # Override the base method, using a different serializer
        # depending on the url parameter (these serializers govern the fields
        # that are accessible to the route, form rendering, validation)
        fidia_type = self.kwargs['fidia_type']
        try:
            return self.serializer_action_classes[fidia_type]
        except (KeyError, AttributeError):
            return super(DataForType, self).get_serializer_class()

    def get_filter_serializer_class(self):
        # returns the list serializer used to display the results
        fidia_type = self.kwargs['fidia_type']
        return self.filter_serializer_classes[fidia_type]

    def get_data_from_fidia(self, fidia_type=None, astroObject=None, survey=None, trait_key=None):
        try:
            # TODO get data from fidia according to the fidia_type (trait-collection/trait/sub-trait/trait-property)
            # TODO should the method call include information on the instance type? (e.g., dmu)
            return []
        except (KeyError, AttributeError):
            _message = "Cannot access data for : %s" % fidia_type
            return Response({'error': _message})

    def create(self, request, fidia_type=None, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        if fidia_type in self.available_keywords:
            _astroObject = serializer.data.get('astroObject')
            _survey = serializer.data.get('survey')
            _trait_key = serializer.data.get('trait_key')
            data = self.get_data_from_fidia(fidia_type=fidia_type, astroObject=_astroObject, survey=_survey, trait_key=_trait_key)
        else:
            # print("%s: '%s'" % (elt.tag, str(elt.text).strip()))
            _message = "fidia_type by must be one of the following values: %s" % self.available_keywords
            return Response({'error': _message})

        completed_data = dict(enumerate(data))
        page = self.paginate_queryset(list(completed_data.values()))

        if page is not None:
            filter_serializer_class = self.get_filter_serializer_class()
            filter_serializer = filter_serializer_class(page, many=True)
            return self.get_paginated_response(filter_serializer.data)

        headers = self.get_success_headers(serializer.data)
        # return each as json using
        filter_serializer_class = self.get_filter_serializer_class()
        filter_serializer = filter_serializer_class(instance=completed_data.values(), many=True)
        return Response(filter_serializer.data, status=status.HTTP_201_CREATED, headers=headers)

DataForType.__doc__ = DATAFOR_DOC_STRING


class SchemaFor(views.APIView):
    # Root view for filter-by, returns available urls for various types of filter
    # (keyword or position)
    def get(self, request, *args, **kwargs):
        return Response({
            'fidia_types': [
                {'type': 'archives', 'url': reverse('sov:schema-for', kwargs={"fidia_type": "archives"}, request=request)},
                {'type': 'traits', 'url': reverse('sov:schema-for', kwargs={"fidia_type": "traits"}, request=request)},
            ]
        })


class SchemaForType(generics.CreateAPIView):
    # Filter by a keyword or position
    queryset = get_archive().values()
    available_keywords = ['archives', 'traits']

    serializer_action_classes = {
        'archives': sov.serializers.SchemaForArchives,
        'traits': sov.serializers.SchemaForTrait,
    }

    filter_serializer_classes = {
        'archives': sov.serializers.ArchiveSchema,
        'traits': sov.serializers.TraitSchema,
    }

    def get_serializer_class(self):
        # Override the base method, using a different serializer
        # depending on the url parameter (these serializers govern the fields
        # that are accessible to the route, form rendering, validation)
        fidia_type = self.kwargs['fidia_type']
        try:
            return self.serializer_action_classes[fidia_type]
        except (KeyError, AttributeError):
            return super(SchemaForType, self).get_serializer_class()

    def get_filter_serializer_class(self):
        # returns the list serializer used to display the results
        fidia_type = self.kwargs['fidia_type']
        return self.filter_serializer_classes[fidia_type]

    def get_schema_from_fidia(self, fidia_type=None, archive=None, astroObject=None, survey=None, trait_key=None):
        try:
            # get fidia trait schema
            print(fidia.known_archives.all())
            # _available_traits = fidia.traits.generic_traits.__all__
            # _trait_schema = []
            # print(fidia.traits.generic_traits.Image.__dict__)

            # return [{'traits': _available_traits, 'trait_schema': _trait_schema}]
            return []
        except (KeyError, AttributeError):
            _message = "Cannot access data for : %s" % fidia_type
            return Response({'error': _message})

    def create(self, request, fidia_type=None, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        if fidia_type in self.available_keywords:
            _archive = serializer.data.get('archive')
            _astroObject = serializer.data.get('astroObject')
            _survey = serializer.data.get('survey')
            _trait_key = serializer.data.get('trait_key')
            data = self.get_schema_from_fidia(fidia_type=fidia_type, archive=_archive, astroObject=_astroObject, survey=_survey, trait_key=_trait_key)
        else:
            # print("%s: '%s'" % (elt.tag, str(elt.text).strip()))
            _message = "fidia_type by must be one of the following values: %s" % self.available_keywords
            return Response({'error': _message})

        completed_data = dict(enumerate(data))
        page = self.paginate_queryset(list(completed_data.values()))

        if page is not None:
            filter_serializer_class = self.get_filter_serializer_class()
            filter_serializer = filter_serializer_class(page, many=True)
            return self.get_paginated_response(filter_serializer.data)

        headers = self.get_success_headers(serializer.data)
        # return each as json using
        filter_serializer_class = self.get_filter_serializer_class()
        filter_serializer = filter_serializer_class(instance=completed_data.values(), many=True)
        return Response(filter_serializer.data, status=status.HTTP_201_CREATED, headers=headers)


# class RootViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
#     """ Viewset for DataBrowser API root. Implements List action only.
#     Lists all surveys, their current versions and total number of objects in that version. """
#
#     def __init__(self, *args, **kwargs):
#         self.surveys = [
#             {"survey": "sami", "count": sami_dr1_sample.ids.__len__(), "current_version": 1.0, "data_releases": {1.0},
#              "astro_objects": {}},
#             {"survey": "gama", "count": 0, "current_version": 0},
#             {"survey": "galah", "count": 0, "current_version": 0}
#         ]
#
#     renderer_classes = (sov.renderers.RootRenderer, renderers.JSONRenderer)
#     permission_classes = [permissions.AllowAny]
#
#     def list(self, request, pk=None, format=None):
#
#         self.breadcrumb_list = ['Single Object Viewer']
#
#         for survey in self.surveys:
#             if survey["survey"] == "sami":
#                 for astro_object in sami_dr1_sample:
#                     url_kwargs = {
#                         'astroobject_pk': str(astro_object),
#                         'survey_pk': 'sami'
#                     }
#                     url = reverse("sov:astroobject-list", kwargs=url_kwargs)
#                     survey["astro_objects"][astro_object] = url
#
#         serializer_class = sov.serializers.RootSerializer
#         serializer = serializer_class(
#             many=False, instance=sami_dr1_sample,
#             context={'request': request, 'surveys': self.surveys},
#         )
#         return Response(serializer.data)
#
#
# class SurveyViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
#     """
#     Viewset for Sample route. Provides List view AND create (post) to download data.
#     Endpoint: list of astroobjects
#     HTML Context: survey string ('sami') and survey catalogue data
#     """
#
#     renderer_classes = (sov.renderers.SurveyRenderer, renderers.JSONRenderer)
#     permission_classes = [permissions.AllowAny]
#     serializer_class = sov.serializers.DownloadSerializer
#
#     def __init__(self, *args, **kwargs):
#         self.catalog = self.traits = ''
#
#     def list(self, request, pk=None, survey_pk=None, format=None, extra_keyword=None):
#
#         self.breadcrumb_list = ['Single Object Viewer', str(survey_pk).upper()]
#
#         try:
#             # TODO ask FIDIA what it's got for survey_pk
#             sami_dr1_sample
#             if survey_pk != "sami":
#                 message = 'Survey does not exist: ' + survey_pk
#                 raise restapi_app.exceptions.CustomValidation(detail=message, field='detail',
#                                                               status_code=status.HTTP_404_NOT_FOUND)
#         except KeyError:
#             return Response(status=status.HTTP_404_NOT_FOUND)
#         except ValueError:
#             return Response(status=status.HTTP_400_BAD_REQUEST)
#
#         # Context (for html page render)
#         self.catalog = json.dumps(sami_dr1_sample.get_feature_catalog_data())
#         self.traits = ar.full_schema(include_subtraits=False, data_class='non-catalog', combine_levels=None,
#                                      verbosity='descriptions', separate_metadata=True)
#
#         # Endpoint-only
#         serializer_class = sov.serializers.SurveySerializer
#         serializer = serializer_class(
#             instance=sami_dr1_sample, many=False,
#             context={'request': request, 'survey': survey_pk}
#         )
#         return Response(serializer.data)
#
#
# class AstroObjectViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
#     """ Viewset for Astroobject. Provides List view only.
#     Endpoint: available traits (plus branches/versions)
#     HTML context: survey string, astroobject, traits and position (ra,dec)"""
#
#     def __init__(self, *args, **kwargs):
#         self.survey = self.astro_object = self.feature_catalog_data = ''
#         # super().__init__()
#
#     renderer_classes = (sov.renderers.AstroObjectRenderer, renderers.JSONRenderer)
#     permission_classes = [permissions.AllowAny]
#
#     def list(self, request, pk=None, survey_pk=None, astroobject_pk=None, format=None):
#
#         self.breadcrumb_list = ['Single Object Viewer', str(survey_pk).upper(), astroobject_pk]
#
#         try:
#             astro_object = sami_dr1_sample[astroobject_pk]
#             assert isinstance(astro_object, fidia.AstronomicalObject)
#         except fidia.exceptions.NotInSample:
#             message = 'Object ' + astroobject_pk + ' Not Found'
#             raise restapi_app.exceptions.CustomValidation(detail=message, field='detail',
#                                                           status_code=status.HTTP_404_NOT_FOUND)
#         except KeyError:
#             return Response(data={}, status=status.HTTP_404_NOT_FOUND)
#         except ValueError:
#             return Response(data={}, status=status.HTTP_400_BAD_REQUEST)
#
#         if survey_pk != "sami":
#             message = 'Survey does not exist: ' + survey_pk
#             raise restapi_app.exceptions.CustomValidation(detail=message, field='detail',
#                                                           status_code=status.HTTP_404_NOT_FOUND)
#         # Context (for html page render)
#         self.survey = survey_pk
#         self.astro_object = astroobject_pk
#         self.feature_catalog_data = astro_object.get_feature_catalog_data()
#
#         schema_catalog = ar.full_schema(include_subtraits=True, data_class='catalog', combine_levels=None,
#                                          verbosity='descriptions', separate_metadata=True)
#
#         schema_non_catalog = ar.full_schema(include_subtraits=True, verbosity='descriptions', data_class='non-catalog',
#                                              combine_levels=None, separate_metadata=True)
#
#         # remove non-catalog traits from catalog schema
#         for key in schema_non_catalog["trait_types"]:
#             if key in schema_catalog["trait_types"]:
#                 schema_catalog["trait_types"].pop(key)
#
#
#         # Endpoint-only
#         serializer_class = sov.serializers.AstroObjectSerializer
#         serializer = serializer_class(
#             instance=astro_object, many=False,
#             context={
#                 'survey': survey_pk,
#                 'astro_object': astroobject_pk,
#                 'request': request,
#                 # 'traits': ar.full_schema(include_subtraits=False, data_class='all', combine_levels=None, verbosity='descriptions', separate_metadata=True),
#                 'non_catalog_traits': schema_non_catalog,
#                 'catalog_traits': schema_catalog,
#                 'position': {'ra': astro_object.ra, 'dec': astro_object.dec},
#                 'overview_catalog': self.feature_catalog_data
#             }
#         )
#         return Response(serializer.data)
#
#
# class TraitViewSet(mixins.ListModelMixin, viewsets.GenericViewSet, sov.helpers.TraitHelper):
#     """ Viewset for Trait. Provides List view only.
#     Endpoint: available properties
#     HTML context: survey string, astroobject, all available branches"""
#
#     def __init__(self, *args, **kwargs):
#
#         # call init method from TraitHelper (superclass)
#         self.breadcrumb_list = []
#         sov.helpers.TraitHelper.__init__(self)
#         # super().__init__()
#
#     permission_classes = [permissions.AllowAny]
#     renderer_classes = (
#         sov.renderers.TraitRenderer, renderers.JSONRenderer, sov.renderers.FITSRenderer)
#
#     def list(self, request, pk=None, survey_pk=None, astroobject_pk=None, trait_pk=None, format=None):
#
#         try:
#             trait = sami_dr1_sample[astroobject_pk][trait_pk]
#             self.breadcrumb_list = ['Single Object Viewer', str(survey_pk).upper(), astroobject_pk,
#                                     trait.get_pretty_name()]
#         except fidia.exceptions.NotInSample:
#             message = 'Object ' + astroobject_pk + ' Not Found'
#             raise restapi_app.exceptions.CustomValidation(detail=message, field='detail',
#                                                           status_code=status.HTTP_404_NOT_FOUND)
#         except fidia.exceptions.UnknownTrait:
#             message = 'Not found: Object ' + astroobject_pk + ' does not have property ' + trait_pk
#             raise restapi_app.exceptions.CustomValidation(detail=message, field='detail',
#                                                           status_code=status.HTTP_404_NOT_FOUND)
#         except KeyError:
#             message = 'Key Error: ' + trait_pk + ' does not exist'
#             raise restapi_app.exceptions.CustomValidation(detail=message, field='detail',
#                                                           status_code=status.HTTP_404_NOT_FOUND)
#         except ValueError:
#             message = 'Value Error: ' + trait_pk + ' does not exist'
#             raise restapi_app.exceptions.CustomValidation(detail=message, field='detail',
#                                                           status_code=status.HTTP_404_NOT_FOUND)
#
#         # Context (for html page render)
#         self.set_attributes(survey_pk=survey_pk, astroobject_pk=astroobject_pk, trait_pk=trait_pk,
#                             trait=trait, ar=ar)
#         self.fidia_type = "trait"
#
#         if isinstance(trait, traits.Map2D):
#             self.trait_2D_map = True
#
#         # Endpoint
#         serializer_class = sov.serializers.TraitSerializer
#         serializer = serializer_class(
#             instance=trait, many=False,
#             context={
#                 'request': request,
#                 'trait_url': self.trait_url,
#                 'trait_class': self.trait_class
#             }
#         )
#
#         return Response(serializer.data)
#
#     def finalize_response(self, request, response, *args, **kwargs):
#         response = super().finalize_response(request, response, *args, **kwargs)
#         if response.accepted_renderer.format == 'fits':
#             trait = sami_dr1_sample[kwargs['astroobject_pk']][kwargs['trait_pk']]
#             filename = "{obj_id}-{trait_key}.fits".format(
#                 obj_id=kwargs['astroobject_pk'],
#                 trait_key=trait.trait_key.ashyphenstr())
#             response['content-disposition'] = "attachment; filename=%s" % filename
#         return response
#
#
# class SubTraitPropertyViewSet(mixins.ListModelMixin, viewsets.GenericViewSet, sov.helpers.TraitHelper):
#     """
#     Dynamic View evaluated on instance type is Trait or Trait property
#     This is only one level
#     """
#     renderer_classes = (sov.renderers.SubTraitPropertyRenderer, renderers.JSONRenderer, sov.renderers.FITSRenderer)
#     permission_classes = [permissions.AllowAny]
#
#     def __init__(self, *args, **kwargs):
#         # call init method from TraitHelper (superclass)
#         self.template = 'sov/trait_property/list.html'
#         sov.helpers.TraitHelper.__init__(self)
#
#     def list(self, request, survey_pk=None, astroobject_pk=None, trait_pk=None, subtraitproperty_pk=None, format=None):
#
#         try:
#             # Determine what we're looking at.
#             # type_for_trait_path requires the trait_key and current "path"
#             path = [subtraitproperty_pk]  # < class 'list'>: ['value']
#             path.insert(0, trait_pk)  # < class 'list'>: ['line_emission_map-HBETA', 'value']
#
#         except:
#             message = 'Not found: Object ' + astroobject_pk + ' trait ' + trait_pk + ' does not have property ' + subtraitproperty_pk
#             raise restapi_app.exceptions.CustomValidation(detail=message, field='detail',
#                                                           status_code=status.HTTP_404_NOT_FOUND)
#
#         # Context (for html page render)
#         try:
#             trait_pointer = sami_dr1_sample[astroobject_pk][trait_pk]
#         except KeyError:
#             _branch = trait_pk.split(":")[1]
#             message = 'No ' + trait_pk + ' data available for ' + astroobject_pk + '. Check the branch and version [' + _branch + '] are correct.'
#             raise restapi_app.exceptions.CustomValidation(detail=message, field='detail',
#                                                           status_code=status.HTTP_404_NOT_FOUND)
#         except fidia.exceptions.UnknownTrait:
#             message = 'Unknown trait: ' + trait_pk
#             raise restapi_app.exceptions.CustomValidation(detail=message, field='detail',
#                                                           status_code=status.HTTP_404_NOT_FOUND)
#
#         self.set_attributes(survey_pk=survey_pk, astroobject_pk=astroobject_pk, trait_pk=trait_pk,
#                             trait=trait_pointer, ar=ar)
#
#         if issubclass(ar.type_for_trait_path(path), Trait):
#             self.template = 'sov/sub_trait/list.html'
#             self.fidia_type = "sub_trait"
#             subtrait_pointer = trait_pointer[subtraitproperty_pk]
#
#             self.trait_2D_map = False
#             if isinstance(subtrait_pointer, traits.Map2D):
#                 self.trait_2D_map = True
#
#             serializer = sov.serializers.TraitSerializer(
#                 instance=subtrait_pointer, many=False,
#                 context={'request': request,
#                          'trait_url': reverse("sov:trait-list",
#                                               kwargs={'survey_pk': survey_pk, 'astroobject_pk': astroobject_pk,
#                                                       'trait_pk': trait_pk, }),
#                          })
#             # Set Breadcrumbs for this method
#             self.breadcrumb_list = ['Data Browser', str(survey_pk).upper(), astroobject_pk,
#                                     trait_pointer.get_pretty_name(),
#                                     subtrait_pointer.get_pretty_name()]
#
#         elif issubclass(ar.type_for_trait_path(path), TraitProperty):
#
#             try:
#                 traitproperty_pointer = getattr(trait_pointer, subtraitproperty_pk)
#             except:
#                 message = 'Not found: Object ' + astroobject_pk + ' trait ' + trait_pk + ' does not have property ' + subtraitproperty_pk
#                 raise restapi_app.exceptions.CustomValidation(detail=message, field='detail',
#                                                               status_code=status.HTTP_404_NOT_FOUND)
#
#             self.template = 'sov/trait_property/list.html'
#             self.fidia_type = "trait_property"
#
#             # Set Breadcrumbs for this method
#             self.breadcrumb_list = ['Data Browser', str(survey_pk).upper(), astroobject_pk,
#                                     trait_pointer.get_pretty_name(),
#                                     traitproperty_pointer.get_pretty_name()]
#
#             self.trait_2D_map = False
#             if isinstance(traitproperty_pointer, traits.Map2D):
#                 self.trait_2D_map = True
#
#             if 'array' in traitproperty_pointer.type and 'string' not in traitproperty_pointer.type:
#                 try:
#                     n_axes = len(traitproperty_pointer.value.shape)
#                 except AttributeError:
#                     pass
#                 except fidia.exceptions.DataNotAvailable:
#                     message = 'No ' + subtraitproperty_pk + ' data available for ' + trait_pk
#                     raise restapi_app.exceptions.CustomValidation(detail=message, field='detail',
#                                                                   status_code=status.HTTP_404_NOT_FOUND)
#                 else:
#                     # the front end visualizer can handle multi-extension data
#                     if n_axes == 2 or n_axes == 3:
#                         self.trait_2D_map = True
#                         # @TODO: Handle arrays other than numpy ndarrays
#
#             serializer = sov.serializers.TraitPropertySerializer(
#                 instance=traitproperty_pointer, many=False,
#                 context={'request': request,
#                          'trait_url': reverse("sov:trait-list",
#                                               kwargs={'survey_pk': survey_pk, 'astroobject_pk': astroobject_pk,
#                                                       'trait_pk': trait_pk, }),
#                          })
#
#         else:
#             raise Exception("An error has occurred.")
#
#         return Response(serializer.data)
#
#     def finalize_response(self, request, response, *args, **kwargs):
#         response = super().finalize_response(request, response, *args, **kwargs)
#         if response.accepted_renderer.format == 'fits':
#             trait = sami_dr1_sample[kwargs['astroobject_pk']][kwargs['trait_pk']]
#             sub_trait = trait[kwargs['subtraitproperty_pk']]
#             filename = "{obj_id}-{trait_key}-{subtrait_key}.fits".format(
#                 obj_id=kwargs['astroobject_pk'],
#                 trait_key=trait.trait_key.ashyphenstr(),
#                 subtrait_key=sub_trait.trait_key.ashyphenstr())
#             response['content-disposition'] = "attachment; filename=%s" % filename
#         return response
#
# class TraitPropertyViewSet(mixins.ListModelMixin, viewsets.GenericViewSet, sov.helpers.TraitHelper):
#     """
#     Final level of nesting - this will provide a level to all those sub-trait/traitproperty views.
#     Might not even need it - may be able to pass through SubTraitProperty Viewset with carefully managed pks
#     """
#     permission_classes = [permissions.AllowAny]
#     renderer_classes = (sov.renderers.SubTraitPropertyRenderer, renderers.JSONRenderer)
#
#     def __init__(self, survey=None, astro_object=None, trait=None, template=None, *args, **kwargs):
#         self.template = 'sov/trait_property/list.html'
#         sov.helpers.TraitHelper.__init__(self)
#
#     def list(self, request, survey_pk=None, astroobject_pk=None, trait_pk=None, subtraitproperty_pk=None,
#              traitproperty_pk=None, format=None):
#
#         self.breadcrumb_list = ['Data Browser', str(survey_pk).upper(), astroobject_pk, trait_pk,
#                                 subtraitproperty_pk, traitproperty_pk]
#
#         # set trait attributes on the renderer context
#         try:
#             trait_pointer = sami_dr1_sample[astroobject_pk][trait_pk]
#         except KeyError:
#             message = "Key not found: " + trait_pk
#             raise restapi_app.exceptions.CustomValidation(detail=message, field='detail',
#                                                           status_code=status.HTTP_404_NOT_FOUND)
#         try:
#             subtrait_pointer = sami_dr1_sample[astroobject_pk][trait_pk][subtraitproperty_pk]
#         except KeyError:
#             message = "Key not found: " + subtraitproperty_pk
#             raise restapi_app.exceptions.CustomValidation(detail=message, field='detail',
#                                                           status_code=status.HTTP_404_NOT_FOUND)
#         try:
#             traitproperty_pointer = getattr(sami_dr1_sample[astroobject_pk][trait_pk][subtraitproperty_pk],
#                                             traitproperty_pk)
#         except Exception:
#             message = "Key not found: " + traitproperty_pk
#             raise restapi_app.exceptions.CustomValidation(detail=message, field='detail',
#                                                           status_code=status.HTTP_404_NOT_FOUND)
#
#         # Context (for html page render)
#         self.set_attributes(survey_pk=survey_pk, astroobject_pk=astroobject_pk, trait_pk=trait_pk,
#                             trait=trait_pointer, ar=ar)
#
#         self.fidia_type = "trait_property"
#         self.subtrait_pretty_name = subtrait_pointer.get_pretty_name()
#         self.sub_trait = subtrait_pointer.trait_name
#
#         self.trait_2D_map = False
#         if isinstance(traitproperty_pointer, traits.Map2D):
#             self.trait_2D_map = True
#
#         if 'array' in traitproperty_pointer.type and 'string' not in traitproperty_pointer.type:
#             try:
#                 n_axes = len(traitproperty_pointer.value.shape)
#             except AttributeError:
#                 pass
#             except fidia.exceptions.DataNotAvailable:
#                 message = 'No ' + subtraitproperty_pk + ' data available for ' + trait_pk
#                 raise restapi_app.exceptions.CustomValidation(detail=message, field='detail',
#                                                               status_code=status.HTTP_404_NOT_FOUND)
#             else:
#                 if n_axes == 2 or n_axes == 3:
#                     self.trait_2D_map = True
#                     # @TODO: Handle arrays other than numpy ndarrays
#
#         serializer = sov.serializers.TraitPropertySerializer(
#             instance=traitproperty_pointer, many=False,
#             context={'request': request,
#                      'trait_url': reverse("sov:trait-list",
#                                           kwargs={'survey_pk': survey_pk, 'astroobject_pk': astroobject_pk,
#                                                   'trait_pk': trait_pk, }),
#                      }
#         )
#
#         self.breadcrumb_list = ['Single Object Viewer', str(survey_pk).upper(), astroobject_pk,
#                                 trait_pointer.get_pretty_name(),
#                                 subtrait_pointer.get_pretty_name(), traitproperty_pointer.get_pretty_name()]
#
#         return Response(serializer.data)
