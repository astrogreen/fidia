from django.utils.text import slugify

from rest_framework import serializers
from rest_framework.reverse import reverse
from rest_framework.validators import UniqueValidator, UniqueTogetherValidator

import documentation.models




class ArticleSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name="documentation:article-detail", lookup_field='slug')
    topic_info = serializers.SerializerMethodField()
    created = serializers.DateTimeField(format="%Y-%m-%d, %H:%M:%S", read_only=True)
    updated = serializers.DateTimeField(format="%Y-%m-%d, %H:%M:%S", read_only=True)

    def get_topic_info(self,obj):
        topic_info = {}
        topic_info['slug'] = obj.topic.slug
        topic_info['id'] = obj.topic.slug
        topic_info['title'] = obj.topic.slug
        return topic_info


    class Meta:
        model = documentation.models.Article
        fields = ('url', 'title', 'content', 'topic', 'topic_info', 'created', 'updated')
        lookup_field = 'slug'
        extra_kwargs = {
            'url': {'lookup_field': 'slug'}
        }
        ordering = ('updated',)




class TopicSerializer(serializers.ModelSerializer):
    articles = ArticleSerializer(many=True, read_only=True)
    url = serializers.HyperlinkedIdentityField(view_name="documentation:topic-detail", lookup_field='slug')
    created = serializers.DateTimeField(format="%Y-%m-%d, %H:%M:%S", read_only=True)
    updated = serializers.DateTimeField(format="%Y-%m-%d, %H:%M:%S", read_only=True)

    class Meta:
        model = documentation.models.Topic
        fields = ('url', 'title', 'articles', 'created', 'updated')
        lookup_field = 'slug'
        extra_kwargs = {
            'url': {'lookup_field': 'slug'}
        }
        ordering = ('id',)
