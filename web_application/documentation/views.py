import itertools
import django.core.exceptions
from rest_framework import views, generics, viewsets, status
from rest_framework.response import Response
from rest_framework.settings import api_settings
from rest_framework.reverse import reverse
from rest_framework.decorators import detail_route, list_route

from hitcount.models import HitCount, Hit
from hitcount.views import HitCountMixin

import restapi_app.renderers
import restapi_app.permissions
import restapi_app.exceptions

import documentation.models
import documentation.serializers

class TopicViewset(viewsets.ModelViewSet):
    serializer_class = documentation.serializers.TopicSerializer
    queryset = documentation.models.Topic.objects.order_by('ordering')
    permission_classes = [restapi_app.permissions.IsAdminOrReadOnly]
    lookup_field = 'slug'
    ordering = ('ordering',)
    pagination_class = None

class ArticleViewset(viewsets.ModelViewSet, HitCountMixin):

    serializer_class = documentation.serializers.ArticleSerializer
    queryset = documentation.models.Article.objects.order_by('-article_order')
    lookup_field = 'id'
    permission_classes = [restapi_app.permissions.IsAdminOrReadOnly]
    pagination_class = None

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)

        # first get the related HitCount object for your model object
        hit_count = HitCount.objects.get_for_object(instance)

        # next, you can attempt to count a hit and get the response
        # you need to pass it the request object as well
        hit_count_response = HitCountMixin.hit_count(request, hit_count)

        # print(hit_count_response)

        return Response(serializer.data)

    def get_serializer_class(self):
        if self.action == 'list':
            return documentation.serializers.ListArticleSerializer
        return documentation.serializers.ArticleSerializer
