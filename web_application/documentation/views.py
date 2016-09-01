import itertools
from rest_framework import views, generics, viewsets, renderers, permissions, mixins
from rest_framework.response import Response
from rest_framework.settings import api_settings
from rest_framework.reverse import reverse
from rest_framework.decorators import detail_route, list_route

import restapi_app.renderers
import restapi_app.permissions

import documentation.models
import documentation.serializers


class TopicViewset(viewsets.ModelViewSet):
    def __init__(self, slug=None, *args, **kwargs):
        # super(TopicViewset, self).__init__()
        self.breadcrumb_list = ['Help Center']

    serializer_class = documentation.serializers.TopicSerializer
    queryset = documentation.models.Topic.objects.all().order_by('id')
    permission_classes = [restapi_app.permissions.IsAdminOrReadOnly]
    lookup_field = 'slug'
    ordering = ('ordering',)

    class TopicRenderer(restapi_app.renderers.ExtendBrowsableAPIRenderer):
        template = 'documentation/topic.html'

    renderer_classes = (TopicRenderer,) + tuple(api_settings.DEFAULT_RENDERER_CLASSES)

    def retrieve(self, request, slug=None, *args, **kwargs):
        # Find the title corresponding to this slug
        topic = documentation.models.Topic.objects.get(slug=slug)
        self.breadcrumb_list = ['Help Center', topic.title]
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)


class ArticleViewset(viewsets.ModelViewSet):
    serializer_class = documentation.serializers.ArticleSerializer
    queryset = documentation.models.Article.objects.all()
    permission_classes = [restapi_app.permissions.IsAdminOrReadOnly]
    lookup_field = 'slug'

    class ArticleRenderer(restapi_app.renderers.ExtendBrowsableAPIRenderer):
        template = 'documentation/article.html'

    renderer_classes = (ArticleRenderer,) + tuple(api_settings.DEFAULT_RENDERER_CLASSES)

#
#
# class DocumentationRoot(generics.ListAPIView):
#     """Declare all the models you wish the documentation route to trawl in the queryset"""
#     # queryset = list(itertools.chain(documentation.models.SAMI.objects.all(), documentation.models.GAMA.objects.all(),
#     #                                 documentation.models.AAODC.objects.all()))
#     queryset = documentation.models.SAMI.objects.all()
#     serializer_class = documentation.serializers.RootSerializer
#
#     # class RootRenderer(restapi_app.renderers.ExtendBrowsableAPIRenderer):
#     #     template = 'documentation/root.html'
#     #
#     # renderer_classes = (RootRenderer, renderers.AdminRenderer,) + tuple(
#     #     api_settings.DEFAULT_RENDERER_CLASSES)
#
#
#
#
#
#
#
# class ArticleRenderer(restapi_app.renderers.ExtendBrowsableAPIRenderer):
#     template = 'documentation/sami/viewset.html'
#
#     def get_context(self, data, accepted_media_type, renderer_context):
#         """ Add reserved keys to the context so the template knows not to iterate over these keys, rather,
#         they will be explicitly positioned. """
#         context = super().get_context(data, accepted_media_type, renderer_context)
#         if hasattr(renderer_context['view'], 'route'):
#             context['route'] = renderer_context['view'].route
#         return context
#
#
# class SAMIDocumentation(viewsets.ModelViewSet):
#     """
#     Viewset handling all SAMI documentation, available only to admin users currently
#     """
#
#     class SAMIDocumentationRenderer(restapi_app.renderers.ExtendBrowsableAPIRenderer):
#         template = 'documentation/sami/viewset.html'
#
#     permission_classes = [restapi_app.permissions.IsAdminOrReadOnly]
#     queryset = documentation.models.SAMI.objects.all()
#     serializer_class = documentation.serializers.SAMISerializer
#
#     renderer_classes = (ArticleRenderer, renderers.AdminRenderer,) + tuple(api_settings.DEFAULT_RENDERER_CLASSES)
#     lookup_field = 'slug'
#     route = {"reverse": 'documentation:sami-docs-list', "name": 'SAMI'}
#
#     def retrieve(self, request, slug=None, *args, **kwargs):
#         self.breadcrumb_list = ['SAMI', slug]
#         instance = self.get_object()
#         serializer = self.get_serializer(instance)
#         return Response(serializer.data)
#
#
# class DataBrowserDocumentation(viewsets.ModelViewSet):
#     """
#     Viewset handling all SAMI documentation, available only to admin users currently
#     """
#     permission_classes = [restapi_app.permissions.IsAdminOrReadOnly]
#     queryset = documentation.models.AAODC.objects.all()
#     serializer_class = documentation.serializers.AAODCSerializer
#     renderer_classes = (ArticleRenderer, renderers.AdminRenderer,) + tuple(api_settings.DEFAULT_RENDERER_CLASSES)
#     lookup_field = 'slug'
#     route = {"reverse": 'documentation:data-browser-docs-list', "name":'Data Browser'}
#
#     def retrieve(self, request, slug=None, *args, **kwargs):
#         self.route = 'data browser'
#         self.breadcrumb_list = ['Data Browser', slug]
#         instance = self.get_object()
#         serializer = self.get_serializer(instance)
#         return Response(serializer.data)
