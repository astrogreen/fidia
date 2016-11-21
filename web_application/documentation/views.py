import itertools
import django.core.exceptions
from rest_framework import views, generics, viewsets, status
from rest_framework.response import Response
from rest_framework.settings import api_settings
from rest_framework.reverse import reverse
from rest_framework.decorators import detail_route, list_route

from hitcount.models import HitCount
from hitcount.views import HitCountMixin

import restapi_app.renderers
import restapi_app.permissions
import restapi_app.exceptions

import documentation.models
import documentation.serializers


class TopicRenderer(restapi_app.renderers.ExtendBrowsableAPIRenderer):
    top_topics = 0
    all_topics = ''
    template = 'documentation/topic.html'

    def get_context(self, data, accepted_media_type, renderer_context):
        context = super().get_context(data, accepted_media_type, renderer_context)
        context['top_articles'] = renderer_context['view'].top_articles
        context['all_topics'] = renderer_context['view'].all_topics
        return context


class ArticleRenderer(restapi_app.renderers.ExtendBrowsableAPIRenderer):
    template = 'documentation/article.html'

    def get_context(self, data, accepted_media_type, renderer_context):
        context = super().get_context(data, accepted_media_type, renderer_context)
        return context


def get_top_articles():
    # get the top topics and pass to renderer context
    available_articles_sorted = []

    for t in HitCount.objects.all().order_by('hits'):
        # get local set of attributes on the t instance
        instance = t.__dict__

        # find the corresponding article in the database, and get attributes of the instance
        _article = documentation.models.Article.objects.get(id=instance['object_pk'])
        _article = _article.__dict__

        # add the relevant topic and topic slug properties
        _article['topic'] = documentation.models.Topic.objects.filter(id=_article['topic_id']).only('title')[0].title
        _article['topic_slug'] = documentation.models.Topic.objects.filter(id=_article['topic_id']).only('slug')[0].slug

        # figure out if topic is hidden
        _topic_hidden = documentation.models.Topic.objects.filter(id=_article['topic_id']).only('title')[0].hidden

        # hide if the topic is hidden, or the article itself is hidden
        if _article['hidden'] is False and _topic_hidden is False:
            available_articles_sorted.append(_article)

    return available_articles_sorted[:10]


def get_all_topics():
    # get all topics and pass to renderer context
    all_topics = []
    for t in documentation.models.Topic.objects.exclude(hidden=True).order_by('ordering'):
        all_topics.append(t.__dict__)
    return all_topics


class TopicViewset(viewsets.ModelViewSet):
    def __init__(self, slug=None, *args, **kwargs):
        self.breadcrumb_list = ['Help Center']
        self.all_topics = get_all_topics()
        self.top_articles = get_top_articles()

    serializer_class = documentation.serializers.TopicSerializer
    queryset = documentation.models.Topic.objects.exclude(hidden=True).order_by('ordering')
    permission_classes = [restapi_app.permissions.IsAdminOrReadOnly]
    lookup_field = 'slug'
    ordering = ('ordering',)
    renderer_classes = (TopicRenderer,) + tuple(api_settings.DEFAULT_RENDERER_CLASSES)

    def retrieve(self, request, slug=None, *args, **kwargs):
        # Find the title corresponding to this slug
        try:
            topic = documentation.models.Topic.objects.get(slug=slug)
        except django.core.exceptions.ObjectDoesNotExist:
            raise restapi_app.exceptions.CustomValidation(detail='Topic does not exist: '+slug, field='detail',
                                                          status_code=status.HTTP_404_NOT_FOUND)
        self.breadcrumb_list = ['Help Center', topic.title]
        instance = self.get_object()
        serializer = self.get_serializer(instance)

        return Response(serializer.data)


class ArticleViewset(viewsets.ModelViewSet, HitCountMixin):
    def __init__(self, slug=None, *args, **kwargs):
        self.all_topics = get_all_topics()

    serializer_class = documentation.serializers.ArticleSerializer
    queryset = documentation.models.Article.objects.exclude(hidden=True)
    lookup_field = 'slug'
    # permission_classes = [restapi_app.permissions.IsSurveyTeamOrAdminElseReadOnly]
    permission_classes = [restapi_app.permissions.IsAdminOrReadOnly]

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

    renderer_classes = (ArticleRenderer,) + tuple(api_settings.DEFAULT_RENDERER_CLASSES)
