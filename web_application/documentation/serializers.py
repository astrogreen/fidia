from django.utils.text import slugify

from rest_framework import serializers
from rest_framework.reverse import reverse
from rest_framework.validators import UniqueValidator, UniqueTogetherValidator

import documentation.models




class ArticleSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name="documentation:article-detail", lookup_field='slug')
    topic_info = serializers.SerializerMethodField()
    # topic = serializers.ChoiceField(choices="obj.topic.")

    def get_topic_info(self,obj):
        topic_info = {}
        topic_info['slug'] = obj.topic.slug
        topic_info['id'] = obj.topic.slug
        topic_info['title'] = obj.topic.slug

        print(vars(obj.topic))

        return topic_info


    class Meta:
        model = documentation.models.Article
        fields = ('url', 'title', 'slug', 'content', 'topic', 'topic_info')
        lookup_field = 'slug'
        extra_kwargs = {
            'url': {'lookup_field': 'slug'}
        }



class TopicSerializer(serializers.ModelSerializer):
    articles = ArticleSerializer(many=True, read_only=True)
    url = serializers.HyperlinkedIdentityField(view_name="documentation:topic-detail", lookup_field='slug')
    # slug = serializers.SlugField(read_only=True, source="slug_generator")

    class Meta:
        model = documentation.models.Topic
        fields = ('url', 'title', 'articles')
        lookup_field = 'slug'
        extra_kwargs = {
            'url': {'lookup_field': 'slug'}
        }


class RootSerializer(serializers.Serializer):
    """ You can re-construct the url of the particular article using the route and the slug"""
    created = serializers.DateTimeField(format="%Y-%m-%d, %H:%M:%S", read_only=True)
    updated = serializers.DateTimeField(format="%Y-%m-%d, %H:%M:%S", read_only=True)
    title = serializers.CharField(default='Title', max_length=100)
    slug = serializers.SlugField(max_length=100, required=True)
    route_name = serializers.CharField(required=True, allow_null=False)

    class Meta:
        fields = ('url', 'created', 'updated', 'title', 'slug', 'route_name')


class DocumentationSerializer(serializers.HyperlinkedModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name="documentation:sami-docs-detail", lookup_field='slug')
    created = serializers.DateTimeField(format="%Y-%m-%d, %H:%M:%S", read_only=True)
    updated = serializers.DateTimeField(format="%Y-%m-%d, %H:%M:%S", read_only=True)
    title = serializers.CharField(default='Title', max_length=100)
    content = serializers.CharField(max_length=100000, required=True, style={'base_template': 'textarea.html'})
    slug = serializers.SlugField(max_length=100, required=True)
    route_name = serializers.CharField(required=True, allow_null=False)

    class Meta:
        fields = ('url', 'created', 'updated', 'title', 'content', 'slug', 'route_name')
        lookup_field = 'slug'
        extra_kwargs = {
            'url': {'lookup_field': 'slug'}
        }


class SAMISerializer(DocumentationSerializer):
    """Subclasses Documentation serializer, setting the model and the unique validation on the slug field"""
    url = serializers.HyperlinkedIdentityField(view_name="documentation:sami-docs-detail", lookup_field='slug')
    slug = serializers.SlugField(max_length=100, required=True, validators=[
        UniqueValidator(queryset=documentation.models.SAMI.objects.all(),
                        message="Slug field already exists.")])

    class Meta:
        model = documentation.models.SAMI


class GAMASerializer(DocumentationSerializer):
    """Subclasses Documentation serializer, setting the model and the unique validation on the slug field"""
    url = serializers.HyperlinkedIdentityField(view_name="documentation:gama-docs-detail", lookup_field='slug')
    slug = serializers.SlugField(max_length=100, required=True, validators=[
        UniqueValidator(queryset=documentation.models.GAMA.objects.all(),
                        message="Slug field already exists.")])

    class Meta:
        model = documentation.models.GAMA


class AAODCSerializer(DocumentationSerializer):
    """Subclasses Documentation serializer, setting the model and the unique validation on the slug field"""
    url = serializers.HyperlinkedIdentityField(view_name="documentation:data-browser-docs-list", lookup_field='slug')
    slug = serializers.SlugField(max_length=100, required=True, validators=[
        UniqueValidator(queryset=documentation.models.AAODC.objects.all(),
                        message="Slug field already exists.")])

    class Meta:
        model = documentation.models.AAODC
