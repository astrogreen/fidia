import json, requests
from django.views.generic import TemplateView
from django.conf import settings
from rest_framework import generics, permissions, renderers, mixins, views, viewsets, status, mixins, exceptions
from rest_framework.response import Response
from rest_framework.settings import api_settings
# from asvo.fidia_samples_archives import sami_dr1_sample, sami_dr1_archive as ar
import restapi_app.exceptions
import restapi_app.serializers
import restapi_app.renderers
import restapi_app.permissions
import restapi_app.models
import sov.serializers
import sov.views

AVAILABLE_SURVEYS = ["sami", "gama"]


class TemplateViewWithStatusCode(TemplateView):
    """
    Adds a status code to the mix. api.html (which all templates extend)
    looks for a status code to determine content or status rendering
    (albeit lazily, if one isn't found it sets to HTTP_200_OK).
    """

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        return self.render_to_response(context, status=status.HTTP_200_OK)


def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


class Surveys(views.APIView):
    """
    Available Surveys page
    """
    permission_classes = (permissions.AllowAny,)

    def get(self, request):
        rootview = sov.views.RootViewSet()

        serializer_class = sov.serializers.RootSerializer
        _dummy = object
        serializer = serializer_class(
            many=False, instance=_dummy,
            context={'request': request, 'surveys': rootview.surveys},
        )

        return Response(serializer.data)


class DataAccess(views.APIView):
    """
    Available Surveys page
    """
    permission_classes = (permissions.AllowAny,)

    def get(self, request):
        surveys = [{
            "survey": "sami",
            # "count": sami_dr1_sample.ids.__len__(),
            "count": 771,
            "current_version": 1.0,
            'data_releases': [1.0, ]}]

        serializer_class = sov.serializers.RootSerializer
        _dummy = object
        serializer = serializer_class(
            many=False, instance=_dummy,
            context={'request': request, 'surveys': surveys},
        )

        return Response(serializer.data)
