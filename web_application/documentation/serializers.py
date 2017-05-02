from django.utils.text import slugify

import documentation.models
from rest_framework import serializers
from rest_framework.reverse import reverse
from rest_framework.validators import UniqueValidator, UniqueTogetherValidator

import documentation.models


class ListArticleSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name="documentation:article-detail", lookup_field='id')
    created = serializers.DateTimeField(format="%Y-%m-%d, %H:%M:%S", read_only=True)
    updated = serializers.DateTimeField(format="%Y-%m-%d, %H:%M:%S", read_only=True)
    topic_info = serializers.SerializerMethodField()
    hit_count = serializers.SerializerMethodField()
    article_order = serializers.IntegerField(default=0)
    id = serializers.IntegerField(allow_null=False)

    def get_topic_info(self, obj):
        topic_info = {'slug': obj.topic.slug, 'id': obj.topic.id, 'title': obj.topic.title}
        return topic_info

    def get_hit_count(self, obj):
        return obj.hit_count.hits

    class Meta:
        model = documentation.models.Article
        fields = ('id', 'url', 'title', 'topic', 'slug', 'topic_info',
                  'created', 'updated', 'hit_count', 'article_order')
        lookup_field = 'id'
        extra_kwargs = {
            'url': {'lookup_field': 'id'}
        }
        ordering = ('article_order',)


class ArticleSerializer(serializers.ModelSerializer):
    """
    Article Serializer for retrieve/update/destroy views, includes
    links to all articles sharing the topic field Foreign Key.

    """

    url = serializers.HyperlinkedIdentityField(view_name="documentation:article-detail", lookup_field='id')
    topic_info = serializers.SerializerMethodField()
    created = serializers.DateTimeField(format="%Y-%m-%d, %H:%M:%S", read_only=True)
    updated = serializers.DateTimeField(format="%Y-%m-%d, %H:%M:%S", read_only=True)
    article_order = serializers.IntegerField(default=0)
    hit_count = serializers.SerializerMethodField()
    all_articles_in_topic = serializers.SerializerMethodField()

    def get_all_articles_in_topic(self, obj):
        if obj.topic.id is not None:
            topic_id = obj.topic.id
            articles_queryset = documentation.models.Article.objects.filter(topic=topic_id)

            serializer = ArticleSlimSerializer(
                instance=articles_queryset,
                many=True,
                read_only=True,
                context={'request': self.context['request']}
            )
            return serializer.data

        else:
            return None

    def get_hit_count(self, obj):
        # # here is an example model with a GenericRelation
        # class MyModel(models.Model, HitCountMixin):
        #     pass
        #
        # # you would access your hit_count like so:
        # my_model = MyModel.objects.get(pk=1)
        # my_model.hit_count.hits                 # total number of hits
        # my_model.hit_count.hits_in_last(days=7) # number of hits in last seven days
        return obj.hit_count.hits

    def get_topic_info(self, obj):
        topic_info = {'slug': obj.topic.slug, 'id': obj.topic.id, 'title': obj.topic.title}
        return topic_info

    class Meta:
        model = documentation.models.Article
        fields = ('id', 'url', 'title', 'content', 'topic', 'all_articles_in_topic',
                  'topic_info', 'created', 'updated', 'hit_count', 'article_order')
        lookup_field = 'id'
        extra_kwargs = {
            'url': {'lookup_field': 'id'}
        }
        ordering = ('article_order',)


class ArticleSlimSerializer(serializers.Serializer):
    """
    Serializer returning only the 'url', 'title', 'topic', 'topic_info' fields for the Article-retrieve route.

    """
    url = serializers.HyperlinkedIdentityField(view_name="documentation:article-detail", lookup_field='id')
    title = serializers.CharField()
    slug = serializers.CharField()
    id = serializers.IntegerField(allow_null=False)

    class Meta:
        fields = ('url', 'title', 'topic', 'id', 'slug')
        lookup_field = 'id'
        extra_kwargs = {
            'url': {'lookup_field': 'id'}
        }


class TopicSerializer(serializers.ModelSerializer):
    articles = ListArticleSerializer(many=True, read_only=True)
    url = serializers.HyperlinkedIdentityField(view_name="documentation:topic-detail", lookup_field='slug')
    created = serializers.DateTimeField(format="%Y-%m-%d, %H:%M:%S", read_only=True)
    updated = serializers.DateTimeField(format="%Y-%m-%d, %H:%M:%S", read_only=True)

    class Meta:
        model = documentation.models.Topic
        fields = ('id', 'url', 'title', 'articles', 'created', 'updated', 'slug')
        lookup_field = 'slug'
        extra_kwargs = {
            'url': {'lookup_field': 'slug'}
        }
        ordering = ('ordering',)
