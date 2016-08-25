from rest_framework import serializers
from rest_framework.reverse import reverse
from rest_framework.validators import UniqueValidator, UniqueTogetherValidator

import documentation.models


class RootSerializer(serializers.Serializer):
    def get_topics(self, obj):
        return self.context['topics']

    topics = serializers.SerializerMethodField()
    class Meta:
        field=('topics')


class DocumentationSerializer(serializers.HyperlinkedModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name="documentation:sami-docs-detail", lookup_field='slug')
    created = serializers.DateTimeField(format="%Y-%m-%d, %H:%M:%S", read_only=True)
    updated = serializers.DateTimeField(format="%Y-%m-%d, %H:%M:%S", read_only=True)
    title = serializers.CharField(default='Title', max_length=100)
    content = serializers.CharField(max_length=100000, required=True, style={'base_template': 'textarea.html'})
    slug = serializers.SlugField(max_length=100, required=True)

    class Meta:
        # model = documentation.models.Documentation
        fields = ('url', 'created', 'updated', 'title', 'content', 'slug')
        lookup_field = 'slug'
        extra_kwargs = {
            'url': {'lookup_field': 'slug'}
        }


class SAMISerializer(DocumentationSerializer):
    """Subclasses Documentation serializer, setting the model and the unique validation on the slug field"""
    slug = serializers.SlugField(max_length=100, required=True, validators=[
        UniqueValidator(queryset=documentation.models.SAMI.objects.all(),
                        message="Slug field already exists.")])

    class Meta:
        model = documentation.models.SAMI


class GAMASerializer(DocumentationSerializer):
    """Subclasses Documentation serializer, setting the model and the unique validation on the slug field"""
    slug = serializers.SlugField(max_length=100, required=True, validators=[
        UniqueValidator(queryset=documentation.models.GAMA.objects.all(),
                        message="Slug field already exists.")])

    class Meta:
        model = documentation.models.GAMA


class AAODCSerializer(DocumentationSerializer):
    """Subclasses Documentation serializer, setting the model and the unique validation on the slug field"""
    slug = serializers.SlugField(max_length=100, required=True, validators=[
        UniqueValidator(queryset=documentation.models.AAODC.objects.all(),
                        message="Slug field already exists.")])

    class Meta:
        model = documentation.models.AAODC
