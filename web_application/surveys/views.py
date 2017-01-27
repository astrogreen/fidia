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


class SurveysViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    """ Viewset for DataBrowser API root. Implements List action only.
    Lists all surveys, their current versions and total number of objects in that version. """

    def __init__(self, *args, **kwargs):
        self.surveys = [
            {"name": "sami", "currentVersion": 1.0, "dataReleases": {1.0},"astroObjects": []},
            {"name": "gama", "currentVersion": 0.0, "dataReleases": {0}, "astroObjects": []}
        ]

    renderer_classes = (renderers.BrowsableAPIRenderer, renderers.JSONRenderer)
    permission_classes = [permissions.AllowAny]

    def list(self, request, pk=None, format=None):

        self.breadcrumb_list = ['Surveys']

        for survey in self.surveys:
            if survey["name"] == "sami":
                survey["astro_objects_arr"] = []
                for astro_object in sami_dr1_sample:
                    # url_kwargs = {
                    #     'astroobject_pk': str(astro_object),
                    #     'survey_pk': 'sami'
                    # }
                    # url = reverse("sov:astroobject-list", kwargs=url_kwargs)
                    survey["astroObjects"].append(str(astro_object))

        serializer_class = sov.serializers.RootSerializer
        serializer = serializer_class(
            many=False, instance=sami_dr1_sample,
            context={'request': request, 'surveys': self.surveys},
        )
        return Response(serializer.data)


class SurveyViewSet(mixins.ListModelMixin, viewsets.GenericViewSet, mixins.CreateModelMixin):
    """
    Viewset for Sample route. Provides List view AND create (post) to download data.
    Endpoint: list of astroobjects
    HTML Context: survey string ('sami') and survey catalogue data
    """

    def __init__(self, *args, **kwargs):
        self.catalog = self.traits = ''

    class SurveyRenderer(restapi_app.renderers.ExtendBrowsableAPIRenderer):
        template = 'surveys/list.html'

        def __repr__(self):
            return 'SurveyRenderer'

        def get_context(self, data, accepted_media_type, renderer_context):
            context = super().get_context(data, accepted_media_type, renderer_context)
            context['catalog'] = renderer_context['view'].catalog
            context['traits'] = renderer_context['view'].traits
            return context

    renderer_classes = (SurveyRenderer, renderers.JSONRenderer)
    permission_classes = [permissions.AllowAny]
    serializer_class = sov.serializers.DownloadSerializer

    def list(self, request, pk=None, survey_pk=None, format=None, extra_keyword=None):

        self.breadcrumb_list = ['Surveys', str(survey_pk).upper()]

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

    def create(self, request, pk=None, survey_pk=None, *args, **kwargs):

        download_data = json.loads(request.POST['download'])

        object_list = (download_data['objects']).split(',')
        product_list = json.loads(download_data['products'])

        # product_list will look like the following:
        #
        # {
        #     "SAMI": [
        #         {
        #             "trait_key": "velocity_map-ionized_gas-recom_comp-V02",
        #             "trait_key_arr": [
        #                 "velocity_map",
        #                 "ionized_gas",
        #                 "recom_comp",
        #                 "V02"
        #             ]
        #         },
        #         {
        #             "trait_key": "extinction_map--recom_comp-V02",
        #             "trait_key_arr": [
        #                 "extinction_map",
        #                 "null",
        #                 "recom_comp",
        #                 "V02"
        #             ]
        #         }
        #     ]
        # }

        trait_path_list = []
        for obj, product in itertools.product(object_list, product_list['SAMI']):

            trait_key_array = product['trait_key_arr']  # type: list
            # Convert "null" and "None" to (Python) None in the list
            while "null" in trait_key_array:
                trait_key_array[trait_key_array.index("null")] = None
            while "None" in trait_key_array:
                trait_key_array[trait_key_array.index("None")] = None

            trait_path = {
                'sample': 'SAMI',
                'object_id': obj,
                'trait_path': [TraitKey(*trait_key_array)]
            }

            trait_path_list.append(trait_path)
        print(trait_path_list)
        tar_stream = fidia_tarfile_helper.fidia_tar_file_generator(sami_dr1_sample, trait_path_list)

        response = StreamingHttpResponse(tar_stream, content_type='application/gzip')
        filename = 'SAMI_data.tar.gz'
        response['content-disposition'] = "attachment; filename=%s" % filename
        response['content-encoding'] = "gzip"

        return response
