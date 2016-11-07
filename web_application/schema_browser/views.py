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
from fidia.traits import Trait, TraitProperty, TraitRegistry, TraitKey


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


