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
    lookup_field = 'slug'
    # permission_classes = [restapi_app.permissions.IsSurveyTeamOrAdminElseReadOnly]
    permission_classes = [restapi_app.permissions.IsAdminOrReadOnly]

    def get_serializer_class(self):
        if self.action == 'list':
            return documentation.serializers.ListArticleSerializer
        return documentation.serializers.ArticleSerializer

    class ArticleRenderer(restapi_app.renderers.ExtendBrowsableAPIRenderer):
        template = 'documentation/article.html'

    renderer_classes = (ArticleRenderer,) + tuple(api_settings.DEFAULT_RENDERER_CLASSES)
