import json
from django.views.generic import TemplateView

from rest_framework import generics, permissions, renderers, mixins, views, viewsets, status, mixins, exceptions
from rest_framework.response import Response
from rest_framework.settings import api_settings
from asvo.fidia_samples_archives import sami_dr1_sample, sami_dr1_archive as ar
import restapi_app.exceptions
import restapi_app.serializers
import restapi_app.renderers
import restapi_app.permissions
import data_browser.serializers

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

        serializer = restapi_app.serializers.ContactFormSerializer

        return Response(data={'serializer': serializer, 'email_status': 'unbound'}, status=status.HTTP_200_OK)

    def post(self, request, format=None):

        serializer = restapi_app.serializers.ContactFormSerializer(data=request.data)
        serializer.is_valid()

        if serializer.is_valid():
            serializer.send()
            serializer_unbound = restapi_app.serializers.ContactFormSerializer
            return Response({"email_status": "success", 'serializer': serializer_unbound}, status=status.HTTP_202_ACCEPTED)

        return Response({"email_status": "error"}, status=status.HTTP_400_BAD_REQUEST)


class Surveys(views.APIView):
    """
    Available Surveys page
    """
    permission_classes = (permissions.AllowAny,)

    class SurveyRenderer(restapi_app.renderers.ExtendBrowsableAPIRenderer):
        template = 'restapi_app/data/surveys.html'
    renderer_classes = (SurveyRenderer,) + tuple(api_settings.DEFAULT_RENDERER_CLASSES)

    def get(self, request):
        surveys = [{"survey": "sami", "count": sami_dr1_sample.ids.__len__(), "current_version": 1.0},
                   {"survey": "gama", "count": 0, "current_version": 0}]

        serializer_class = data_browser.serializers.RootSerializer
        _dummy = object
        serializer = serializer_class(
            many=False, instance=_dummy,
            context={'request': request, 'surveys': surveys},
        )

        return Response(serializer.data)


class Tools(views.APIView):
    """
    Available Surveys page
    """
    permission_classes = (permissions.AllowAny,)

    class ToolRenderer(restapi_app.renderers.ExtendBrowsableAPIRenderer):
        template = 'restapi_app/tools/tools.html'
    renderer_classes = (ToolRenderer,) + tuple(api_settings.DEFAULT_RENDERER_CLASSES)

    def get(self, request):
        samples = AVAILABLE_SURVEYS

        serializer_class = data_browser.serializers.RootSerializer
        _dummy = object
        serializer = serializer_class(
            many=False, instance=_dummy,
            context={'request': request, 'surveys': samples},
        )

        return Response(serializer.data)

