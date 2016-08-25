from rest_framework import serializers
from rest_framework.reverse import reverse
from rest_framework.validators import UniqueValidator, UniqueTogetherValidator

import documentation.models


class DocumentationSerializer(serializers.HyperlinkedModelSerializer):

    url = serializers.HyperlinkedIdentityField(view_name="documentation:sami-docs-detail", lookup_field='slug')
    created = serializers.DateTimeField(format="%Y-%m-%d, %H:%M:%S", read_only=True)
    updated = serializers.DateTimeField(format="%Y-%m-%d, %H:%M:%S", read_only=True)
    title = serializers.CharField(default='Title', max_length=100)
    content = serializers.CharField(max_length=100000, required=True, style={'base_template': 'textarea.html'})
    slug = serializers.SlugField(max_length=20, required=True)

    class Meta:
        # model = documentation.models.Documentation
        fields = ('url', 'created', 'updated', 'title', 'content', 'slug')
        lookup_field = 'slug'
        extra_kwargs = {
            'url': {'lookup_field': 'slug'}
        }


class SAMIDocumentationSerializer(DocumentationSerializer):
    """Subclasses Documentation serializer, setting the model and the unique validation on the slug field"""
    slug = serializers.SlugField(max_length=20, required=True, validators=[
        UniqueValidator(queryset=documentation.models.SAMIDocumentation.objects.all(),
                        message="Slug field already exists.")])

    class Meta:
        model = documentation.models.SAMIDocumentation
