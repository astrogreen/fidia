import json

from rest_framework import generics, permissions, renderers, mixins, views, viewsets, status, mixins, exceptions
from rest_framework.response import Response

import restapi_app.exceptions
import restapi_app.serializers
import restapi_app.renderers
import restapi_app.permissions


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

        return Response({'serializer': serializer})

    def post(self, request, format=None):

        serializer = restapi_app.serializers.ContactFormSerializer(data=request.data)
        serializer.is_valid()

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_202_ACCEPTED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
