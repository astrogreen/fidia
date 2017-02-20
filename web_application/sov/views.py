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

import sov.serializers
import sov.renderers
import sov.mixins
import sov.helpers

import fidia.exceptions
from fidia.traits import Trait, TraitProperty, TraitKey
from fidia import traits

import fidia_tarfile_helper

log = logging.getLogger(__name__)


class RootViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    """ Viewset for DataBrowser API root. Implements List action only.
    Lists all surveys, their current versions and total number of objects in that version. """

    def __init__(self, *args, **kwargs):
        self.surveys = [
            {"survey": "sami", "count": sami_dr1_sample.ids.__len__(), "current_version": 1.0, "data_releases": {1.0},
             "astro_objects": {}},
            {"survey": "gama", "count": 0, "current_version": 0},
            {"survey": "galah", "count": 0, "current_version": 0}
        ]

    renderer_classes = (sov.renderers.RootRenderer, renderers.JSONRenderer)
    permission_classes = [permissions.AllowAny]

    def list(self, request, pk=None, format=None):

        self.breadcrumb_list = ['Single Object Viewer']

        for survey in self.surveys:
            if survey["survey"] == "sami":
                for astro_object in sami_dr1_sample:
                    url_kwargs = {
                        'astroobject_pk': str(astro_object),
                        'survey_pk': 'sami'
                    }
                    url = reverse("sov:astroobject-list", kwargs=url_kwargs)
                    survey["astro_objects"][astro_object] = url

        serializer_class = sov.serializers.RootSerializer
        serializer = serializer_class(
            many=False, instance=sami_dr1_sample,
            context={'request': request, 'surveys': self.surveys},
        )
        return Response(serializer.data)


class SurveyViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    """
    Viewset for Sample route. Provides List view AND create (post) to download data.
    Endpoint: list of astroobjects
    HTML Context: survey string ('sami') and survey catalogue data
    """

    renderer_classes = (sov.renderers.SurveyRenderer, renderers.JSONRenderer)
    permission_classes = [permissions.AllowAny]
    serializer_class = sov.serializers.DownloadSerializer

    def __init__(self, *args, **kwargs):
        self.catalog = self.traits = ''

    def list(self, request, pk=None, survey_pk=None, format=None, extra_keyword=None):

        self.breadcrumb_list = ['Single Object Viewer', str(survey_pk).upper()]

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
        self.traits = ar.full_schema(include_subtraits=False, data_class='non-catalog', combine_levels=None,
                                     verbosity='descriptions', separate_metadata=True)

        # Endpoint-only
        serializer_class = sov.serializers.SurveySerializer
        serializer = serializer_class(
            instance=sami_dr1_sample, many=False,
            context={'request': request, 'survey': survey_pk}
        )
        return Response(serializer.data)


class AstroObjectViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    """ Viewset for Astroobject. Provides List view only.
    Endpoint: available traits (plus branches/versions)
    HTML context: survey string, astroobject, traits and position (ra,dec)"""

    def __init__(self, *args, **kwargs):
        self.survey = self.astro_object = self.feature_catalog_data = ''
        # super().__init__()

    renderer_classes = (sov.renderers.AstroObjectRenderer, renderers.JSONRenderer)
    permission_classes = [permissions.AllowAny]

    def list(self, request, pk=None, survey_pk=None, astroobject_pk=None, format=None):

        self.breadcrumb_list = ['Single Object Viewer', str(survey_pk).upper(), astroobject_pk]

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

        schema_catalog = ar.full_schema(include_subtraits=True, data_class='catalog', combine_levels=None,
                                         verbosity='descriptions', separate_metadata=True)

        schema_non_catalog = ar.full_schema(include_subtraits=True, verbosity='descriptions', data_class='non-catalog',
                                             combine_levels=None, separate_metadata=True)

        # remove non-catalog traits from catalog schema
        for key in schema_non_catalog["trait_types"]:
            if key in schema_catalog["trait_types"]:
                schema_catalog["trait_types"].pop(key)


        # Endpoint-only
        serializer_class = sov.serializers.AstroObjectSerializer
        serializer = serializer_class(
            instance=astro_object, many=False,
            context={
                'survey': survey_pk,
                'astro_object': astroobject_pk,
                'request': request,
                # 'traits': ar.full_schema(include_subtraits=False, data_class='all', combine_levels=None, verbosity='descriptions', separate_metadata=True),
                'non_catalog_traits': schema_non_catalog,
                'catalog_traits': schema_catalog,
                'position': {'ra': astro_object.ra, 'dec': astro_object.dec}
            }
        )
        return Response(serializer.data)


class TraitViewSet(mixins.ListModelMixin, viewsets.GenericViewSet, sov.helpers.TraitHelper):
    """ Viewset for Trait. Provides List view only.
    Endpoint: available properties
    HTML context: survey string, astroobject, all available branches"""

    def __init__(self, *args, **kwargs):

        # call init method from TraitHelper (superclass)
        self.breadcrumb_list = []
        sov.helpers.TraitHelper.__init__(self)
        # super().__init__()

    permission_classes = [permissions.AllowAny]
    renderer_classes = (
        sov.renderers.TraitRenderer, renderers.JSONRenderer, sov.renderers.FITSRenderer)

    def list(self, request, pk=None, survey_pk=None, astroobject_pk=None, trait_pk=None, format=None):

        try:
            trait = sami_dr1_sample[astroobject_pk][trait_pk]
            self.breadcrumb_list = ['Single Object Viewer', str(survey_pk).upper(), astroobject_pk,
                                    trait.get_pretty_name()]
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
        serializer_class = sov.serializers.TraitSerializer
        serializer = serializer_class(
            instance=trait, many=False,
            context={
                'request': request,
                'trait_url': self.trait_url,
                'trait_class': self.trait_class
            }
        )

        return Response(serializer.data)

    def finalize_response(self, request, response, *args, **kwargs):
        response = super().finalize_response(request, response, *args, **kwargs)
        if response.accepted_renderer.format == 'fits':
            trait = sami_dr1_sample[kwargs['astroobject_pk']][kwargs['trait_pk']]
            filename = "{obj_id}-{trait_key}.fits".format(
                obj_id=kwargs['astroobject_pk'],
                trait_key=trait.trait_key.ashyphenstr())
            response['content-disposition'] = "attachment; filename=%s" % filename
        return response


class SubTraitPropertyViewSet(mixins.ListModelMixin, viewsets.GenericViewSet, sov.helpers.TraitHelper):
    """
    Dynamic View evaluated on instance type is Trait or Trait property
    This is only one level
    """
    renderer_classes = (sov.renderers.SubTraitPropertyRenderer, renderers.JSONRenderer)
    permission_classes = [permissions.AllowAny]

    def __init__(self, *args, **kwargs):
        # call init method from TraitHelper (superclass)
        self.template = 'sov/trait_property/list.html'
        sov.helpers.TraitHelper.__init__(self)

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
            message = 'No ' + trait_pk + ' data available for ' + astroobject_pk + '. Check the branch and version [' + _branch + '] are correct.'
            raise restapi_app.exceptions.CustomValidation(detail=message, field='detail',
                                                          status_code=status.HTTP_404_NOT_FOUND)
        except fidia.exceptions.UnknownTrait:
            message = 'Unknown trait: ' + trait_pk
            raise restapi_app.exceptions.CustomValidation(detail=message, field='detail',
                                                          status_code=status.HTTP_404_NOT_FOUND)

        self.set_attributes(survey_pk=survey_pk, astroobject_pk=astroobject_pk, trait_pk=trait_pk,
                            trait=trait_pointer, ar=ar)

        if issubclass(ar.type_for_trait_path(path), Trait):
            self.template = 'sov/sub_trait/list.html'
            self.fidia_type = "sub_trait"
            subtrait_pointer = trait_pointer[subtraitproperty_pk]

            self.trait_2D_map = False
            if isinstance(subtrait_pointer, traits.Map2D):
                self.trait_2D_map = True

            serializer = sov.serializers.TraitSerializer(
                instance=subtrait_pointer, many=False,
                context={'request': request,
                         'trait_url': reverse("sov:trait-list",
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

            self.template = 'sov/trait_property/list.html'
            self.fidia_type = "trait_property"

            # Set Breadcrumbs for this method
            self.breadcrumb_list = ['Data Browser', str(survey_pk).upper(), astroobject_pk,
                                    trait_pointer.get_pretty_name(),
                                    traitproperty_pointer.get_pretty_name()]

            self.trait_2D_map = False
            if isinstance(traitproperty_pointer, traits.Map2D):
                self.trait_2D_map = True

            if 'array' in traitproperty_pointer.type and 'string' not in traitproperty_pointer.type:
                try:
                    n_axes = len(traitproperty_pointer.value.shape)
                except AttributeError:
                    pass
                except fidia.exceptions.DataNotAvailable:
                    message = 'No ' + subtraitproperty_pk + ' data available for ' + trait_pk
                    raise restapi_app.exceptions.CustomValidation(detail=message, field='detail',
                                                                  status_code=status.HTTP_404_NOT_FOUND)
                else:
                    # the front end visualizer can handle multi-extension data
                    if n_axes == 2 or n_axes == 3:
                        self.trait_2D_map = True
                        # @TODO: Handle arrays other than numpy ndarrays

            serializer = sov.serializers.TraitPropertySerializer(
                instance=traitproperty_pointer, many=False,
                context={'request': request,
                         'trait_url': reverse("sov:trait-list",
                                              kwargs={'survey_pk': survey_pk, 'astroobject_pk': astroobject_pk,
                                                      'trait_pk': trait_pk, }),
                         })

        else:
            raise Exception("An error has occurred.")

        return Response(serializer.data)


class TraitPropertyViewSet(mixins.ListModelMixin, viewsets.GenericViewSet, sov.helpers.TraitHelper):
    """
    Final level of nesting - this will provide a level to all those sub-trait/traitproperty views.
    Might not even need it - may be able to pass through SubTraitProperty Viewset with carefully managed pks
    """
    permission_classes = [permissions.AllowAny]
    renderer_classes = (sov.renderers.SubTraitPropertyRenderer, renderers.JSONRenderer)

    def __init__(self, survey=None, astro_object=None, trait=None, template=None, *args, **kwargs):
        self.template = 'sov/trait_property/list.html'
        sov.helpers.TraitHelper.__init__(self)

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
        self.sub_trait = subtrait_pointer.trait_name

        self.trait_2D_map = False
        if isinstance(traitproperty_pointer, traits.Map2D):
            self.trait_2D_map = True

        if 'array' in traitproperty_pointer.type and 'string' not in traitproperty_pointer.type:
            try:
                n_axes = len(traitproperty_pointer.value.shape)
            except AttributeError:
                pass
            except fidia.exceptions.DataNotAvailable:
                message = 'No ' + subtraitproperty_pk + ' data available for ' + trait_pk
                raise restapi_app.exceptions.CustomValidation(detail=message, field='detail',
                                                              status_code=status.HTTP_404_NOT_FOUND)
            else:
                if n_axes == 2:
                    self.trait_2D_map = True
                    # @TODO: Handle arrays other than numpy ndarrays

        serializer = sov.serializers.TraitPropertySerializer(
            instance=traitproperty_pointer, many=False,
            context={'request': request,
                     'trait_url': reverse("sov:trait-list",
                                          kwargs={'survey_pk': survey_pk, 'astroobject_pk': astroobject_pk,
                                                  'trait_pk': trait_pk, }),
                     }
        )

        self.breadcrumb_list = ['Single Object Viewer', str(survey_pk).upper(), astroobject_pk,
                                trait_pointer.get_pretty_name(),
                                subtrait_pointer.get_pretty_name(), traitproperty_pointer.get_pretty_name()]

        return Response(serializer.data)
