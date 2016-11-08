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

    class TraitRenderer(restapi_app.renderers.ExtendBrowsableAPIRenderer):
        pass

    renderer_classes = (TraitRenderer,) + tuple(api_settings.DEFAULT_RENDERER_CLASSES)

    def list(self, request, pk=None, survey_pk=None, trait_pk=None, format=None):
        self.breadcrumb_list = [str(survey_pk).upper(), str(trait_pk)]

        try:

            trait_registry = ar.available_traits
            default_trait_key = trait_registry.update_key_with_defaults(trait_pk)
            trait_class = trait_registry.retrieve_with_key(default_trait_key)

        except KeyError:
            return Response(status=status.HTTP_404_NOT_FOUND)
        except ValueError:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        serializer = schema_browser.serializers.TraitSerializer(
            instance=trait_class, many=False,
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

    class DynamicRenderer(restapi_app.renderers.ExtendBrowsableAPIRenderer):
        pass

    renderer_classes = (DynamicRenderer,) + tuple(api_settings.DEFAULT_RENDERER_CLASSES)

    def list(self, request, pk=None, survey_pk=None, trait_pk=None, dynamic_pk=None, format=None):
        self.breadcrumb_list = [str(survey_pk).upper(), str(trait_pk), str(dynamic_pk)]

        try:

            # get trait_class
            trait_registry = ar.available_traits
            default_trait_key = trait_registry.update_key_with_defaults(trait_pk)
            # print('default_trait_key: ' + str(default_trait_key))
            trait_class = trait_registry.retrieve_with_key(default_trait_key)
            # print('trait_class: ' + str(trait_class))

            # get the schema for this trait class
            trait_class_schema = trait_class.full_schema(verbosity='descriptions')

            # figure out if sub-trait, sub-trait/trait-property or trait-property
            dyn_arr = dynamic_pk.split('/')
            path = [dyn_arr[0]]  # < class 'list'>: ['value']
            path.insert(0, str(default_trait_key))  # < class 'list'>: ['line_emission_map-HBETA', 'value']

            if issubclass(ar.type_for_trait_path(path), Trait):
                # sub-trait - make a TraitPath object and get the sub-trait class
                stp = TraitPath(path)

                sub_trait_class = stp.get_trait_class_for_archive(ar)
                dynamic_obj = sub_trait_class.full_schema(verbosity='descriptions')
                dynamic_type = 'sub_trait'

                if len(dyn_arr) > 1:
                    # has a trait property, update
                    _trait_property_key = dyn_arr[1]

                    sub_trait_schema = sub_trait_class.full_schema(verbosity='descriptions')
                    dynamic_obj = sub_trait_schema["trait_properties"][_trait_property_key]
                    dynamic_type = 'trait_property'
            else:
                # trait property
                dynamic_type = 'trait_property'
                dynamic_obj = trait_class_schema["trait_properties"][dyn_arr[0]]

        # except KeyError:
        #     return Response(status=status.HTTP_404_NOT_FOUND)
        # except ValueError:
        #     return Response(status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            message = str(e)
            raise restapi_app.exceptions.CustomValidation(detail=message, field='detail',
                                                          status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

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
