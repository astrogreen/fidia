from rest_framework import views, generics, viewsets, renderers, permissions
from rest_framework.settings import api_settings

import restapi_app.renderers

import documentation.models
import documentation.serializers


class SAMIDocumentation(viewsets.ModelViewSet):
    """
    Viewset handling all SAMI documentation, available only to admin users currently
    """
    permission_classes = [permissions.IsAdminUser]
    queryset = documentation.models.Documentation.objects.all()
    serializer_class = documentation.serializers.DocumentationSerializer
    renderer_classes = (restapi_app.renderers.ExtendBrowsableAPIRenderer, ) + tuple(api_settings.DEFAULT_RENDERER_CLASSES)
    lookup_field = 'slug'
