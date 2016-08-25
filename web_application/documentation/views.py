from rest_framework import views, generics, viewsets, renderers, permissions
from rest_framework.response import Response
from rest_framework.settings import api_settings
from rest_framework.reverse import reverse
from rest_framework.decorators import detail_route, list_route

import restapi_app.renderers
import restapi_app.permissions

import documentation.models
import documentation.serializers


class SAMIDocumentation(viewsets.ModelViewSet):
    """
    Viewset handling all SAMI documentation, available only to admin users currently
    """

    class SAMIDocumentationRenderer(restapi_app.renderers.ExtendBrowsableAPIRenderer):
        template = 'documentation/sami/viewset.html'

    permission_classes = [restapi_app.permissions.IsAdminOrReadOnly]
    queryset = documentation.models.SAMIDocumentation.objects.all()
    serializer_class = documentation.serializers.SAMIDocumentationSerializer
    renderer_classes = (SAMIDocumentationRenderer, renderers.AdminRenderer,) + tuple(api_settings.DEFAULT_RENDERER_CLASSES)
    lookup_field = 'slug'

    def retrieve(self, request, slug=None, *args, **kwargs):
        self.breadcrumb_list = ['SAMI', slug]
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)
