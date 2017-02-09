import random, collections, logging, json, requests, zipfile, io
import django.core.exceptions
from django.contrib.auth.models import User
from django.conf import settings
from django.http import HttpResponse

from asvo.fidia_samples_archives import sami_dr1_sample, sami_dr1_archive as ar

from rest_framework import generics, permissions, renderers, mixins, views, viewsets, status, mixins, exceptions
from rest_framework.response import Response
from rest_framework.settings import api_settings
from rest_framework import serializers, mixins, status
from rest_framework.reverse import reverse

import restapi_app.permissions
import restapi_app.exceptions
import restapi_app.renderers
import restapi_app.utils.helpers

import schema_browser.serializers

import data_browser.views

import fidia.exceptions
from fidia.traits import Trait, TraitProperty, TraitRegistry, TraitKey, TraitPath


class SchemaViewSet(data_browser.views.RootViewSet):
    class SchemaRenderer(restapi_app.renderers.ExtendBrowsableAPIRenderer):
        template = 'schema_browser/root.html'

    renderer_classes = (SchemaRenderer,) + tuple(api_settings.DEFAULT_RENDERER_CLASSES)

    def list(self, request, pk=None, format=None):
        # Request available samples from FIDIA
        surveys = [{"survey": "sami", "count": sami_dr1_sample.ids.__len__(), "current_version": 1.0}]

        serializer_class = schema_browser.serializers.SchemaSerializer
        serializer = serializer_class(
            many=False, instance=sami_dr1_sample,
            context={'request': request, 'surveys': surveys},
        )
        return Response(serializer.data)


class SurveyViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    class SampleRenderer(restapi_app.renderers.ExtendBrowsableAPIRenderer):
        template = 'schema_browser/survey.html'

    renderer_classes = (SampleRenderer,) + tuple(api_settings.DEFAULT_RENDERER_CLASSES)

    def list(self, request, pk=None, survey_pk=None, format=None):

        self.breadcrumb_list = [str(survey_pk).upper()]

        if survey_pk == 'gama':
            return Response({"sample": "gama", "in_progress": True})

        try:
            ar
        except KeyError:
            return Response(status=status.HTTP_404_NOT_FOUND)
        except ValueError:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        serializer = schema_browser.serializers.SurveySerializer(
            instance=ar, many=False,
            context={
                'survey': survey_pk,
                'request': request
            }
        )
        return Response(serializer.data)


class TraitViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    """
    Schema Browser Trait Viewset providing List route only. Returns schema for a survey_pk and trait_pk.
    """

    def __init__(self, *args, **kwargs):
        self.full_trait_schema = {}
        self.survey = self.trait_name = self.trait_class = self.trait_qualifier = self.trait_pretty_name = self.branch = self.version = ''
        super().__init__(*args, **kwargs)

    class TraitRenderer(restapi_app.renderers.ExtendBrowsableAPIRenderer):
        template = 'schema_browser/trait.html'

        def get_context(self, data, accepted_media_type, renderer_context):
            context = super().get_context(data, accepted_media_type, renderer_context)
            context['survey'] = renderer_context['view'].survey
            context['trait_name'] = renderer_context['view'].trait_name
            context['trait_class'] = renderer_context['view'].trait_class
            context['trait_type'] = renderer_context['view'].trait_class
            context['trait_qualifier'] = renderer_context['view'].trait_qualifier
            context['trait_pretty_name'] = renderer_context['view'].trait_pretty_name
            context['full_trait_schema'] = renderer_context['view'].full_trait_schema
            context['branch'] = renderer_context['view'].branch
            context['version'] = renderer_context['view'].version
            return context

    renderer_classes = (TraitRenderer,) + tuple(api_settings.DEFAULT_RENDERER_CLASSES)

    def list(self, request, pk=None, survey_pk=None, trait_pk=None, format=None):

        # try:

        # trait_registry = ar.available_traits
        # default_trait_key = trait_registry.update_key_with_defaults(trait_pk)
        # trait_class = trait_registry.retrieve_with_key(default_trait_key)
        #
        # assert issubclass(trait_class, Trait), \
        #     "TraitSerializer must have an instance of fidia.Trait, " + \
        #     "not '%s': try TraitSerializer(instance=trait)" % trait_class
        #
        # trait_schema = trait_class.full_schema(verbosity='descriptions')

        # HACK: trait_schema contains only the trait_class schema, with no qualifier information
        # instead, call the full schema and pick out the necessary piece?

        full_schema = ar.full_schema(include_subtraits=True, data_class='all', combine_levels=None,
                                     verbosity='descriptions', separate_metadata=True)

        # get class and qualifier from url key
        _class = trait_pk.split('-')[0]

        if len(trait_pk.split('-')) == 1:
            _class = trait_pk.split(':')[0]

        if len(trait_pk.split('-')) > 1:
            _qualifier = trait_pk.split('-')[1].split(':')[0]
            _trait_name = _class + '-' + _qualifier
        else:
            _qualifier = None
            _trait_name = _class

        # get schema for trait
        full_trait_schema = full_schema["trait_types"][_class]["trait_qualifiers"][_qualifier]

        self.trait_pretty_name = full_trait_schema["pretty_name-trait_name"]

        # get default branch and version
        _default_branch = full_trait_schema["default_branch"]
        _default_version = full_trait_schema["branches"][_default_branch]["default_version"]

        # find branch/version info - if none return _branch and _version
        if len(trait_pk.split(':')) > 1:
            _branch = trait_pk.split(':')[1]
            if len(_branch.split('(')) > 1:
                _branch = trait_pk.split(':')[1].split('(')[0]
                _version = trait_pk.split('(')[1].split(')')[0]
            else:
                _version = _default_version
        else:
            _branch = _default_branch
            _version = _default_version

        trait_schema = full_trait_schema["branches"][_branch]["versions"][_version]["trait"]

        # set context for html render
        self.breadcrumb_list = [str(survey_pk).upper(), full_trait_schema["pretty_name-trait_name"]]
        self.full_trait_schema = full_trait_schema
        self.survey = survey_pk
        self.trait_name = _trait_name
        self.trait_class = _class
        self.trait_qualifier = _qualifier
        self.branch = _branch
        self.version = _version

        # except KeyError:
        #     return Response(status=status.HTTP_404_NOT_FOUND)
        # except ValueError:
        #     return Response(status=status.HTTP_400_BAD_REQUEST)

        serializer = schema_browser.serializers.TraitSerializer(
            instance=trait_schema, many=False,
            context={
                'survey': survey_pk,
                'trait': trait_pk,
                'request': request
            }
        )

        return Response(serializer.data)


class DynamicViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    """
    Schema Browser Dynamic Viewset providing List route only. Returns schema for a survey_pk / trait_pk / sub_trait or trait_property_pk.
    """
    def __init__(self, *args, **kwargs):
        self.full_trait_schema = {}
        self.survey = self.trait_name = self.trait_class = self.trait_qualifier = self.trait_pretty_name = self.branch = self.version = ''
        super().__init__(*args, **kwargs)

    class DynamicRenderer(restapi_app.renderers.ExtendBrowsableAPIRenderer):
        template = 'schema_browser/dynamic.html'

        def get_context(self, data, accepted_media_type, renderer_context):
            context = super().get_context(data, accepted_media_type, renderer_context)
            context['survey'] = renderer_context['view'].survey
            return context

    renderer_classes = (DynamicRenderer,) + tuple(api_settings.DEFAULT_RENDERER_CLASSES)

    def list(self, request, pk=None, survey_pk=None, trait_pk=None, dynamic_pk=None, format=None):
        self.breadcrumb_list = [str(survey_pk).upper()]
        self.url_list = []

        try:
            # get trait_class
            trait_registry = ar.available_traits
            default_trait_key = trait_registry.update_key_with_defaults(trait_pk)
            trait_class = trait_registry.retrieve_with_key(default_trait_key)

            # get the schema for this trait class
            trait_class_schema = trait_class.full_schema(verbosity='descriptions')
            self.breadcrumb_list.append(trait_class_schema["pretty_name"])

            # figure out if sub-trait, sub-trait/trait-property or trait-property
            dyn_arr = dynamic_pk.split('/')

            path = [dyn_arr[0]]  # < class 'list'>: ['value']
            path.insert(0, str(default_trait_key))  # < class 'list'>: ['line_emission_map-HBETA', 'value']

            if issubclass(ar.type_for_trait_path(path), Trait):
                # sub-trait - make a TraitPath object and get the sub-trait class
                stp = TraitPath(path)
                sub_trait_class = stp.get_trait_class_for_archive(ar)
                dynamic_obj = sub_trait_class.full_schema(verbosity='descriptions')

                self.breadcrumb_list.append(dynamic_obj["pretty_name"])
                self.url_list.append(reverse('schema_browser:dynamic-list',
                                             kwargs={'survey_pk': survey_pk, 'trait_pk': trait_pk,
                                                     'dynamic_pk': dyn_arr[0]}))
                dynamic_type = 'sub_trait'

                if len(dyn_arr) > 1:
                    # has a trait property, update
                    _trait_property_key = dyn_arr[1]

                    sub_trait_schema = sub_trait_class.full_schema(verbosity='descriptions')
                    dynamic_obj = sub_trait_schema["trait_properties"][_trait_property_key]
                    self.breadcrumb_list.append(dynamic_obj["pretty_name"])
                    self.url_list.append(reverse('schema_browser:dynamic-list',
                                                 kwargs={'survey_pk': survey_pk, 'trait_pk': trait_pk,
                                                         'dynamic_pk': dynamic_pk}))
                    dynamic_type = 'trait_property'
            else:
                # trait property
                dynamic_obj = trait_class_schema["trait_properties"][dyn_arr[0]]
                self.breadcrumb_list.append(dynamic_obj["pretty_name"])
                self.url_list.append(reverse('schema_browser:dynamic-list',
                                             kwargs={'survey_pk': survey_pk, 'trait_pk': trait_pk,
                                                     'dynamic_pk': dynamic_pk}))
                dynamic_type = 'trait_property'

        except KeyError:
            return Response(status=status.HTTP_404_NOT_FOUND)
        except ValueError:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            message = str(e)
            raise restapi_app.exceptions.CustomValidation(detail=message, field='detail',
                                                          status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.survey = survey_pk

        serializer = schema_browser.serializers.DynamicSerializer(
            instance=dynamic_obj, many=False,
            context={
                'survey': survey_pk,
                'trait': trait_pk,
                'request': request,
                'dynamic_pk': dynamic_pk,
                'dynamic_type': dynamic_type,
            }
        )
        return Response(serializer.data)
