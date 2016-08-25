from django.core.urlresolvers import NoReverseMatch
from rest_framework import serializers
import documentation.models


from rest_framework.relations import HyperlinkedIdentityField
from rest_framework.reverse import reverse

# class ParameterisedHyperlinkedIdentityField(HyperlinkedIdentityField):
#     """
#     Represents the instance, or a property on the instance, using hyperlinking.
#
#     lookup_fields is a tuple of tuples of the form:
#         ('model_field', 'url_parameter')
#     """
#     lookup_fields = (('pk', 'pk'),)
#
#     def __init__(self, *args, **kwargs):
#         self.lookup_fields = kwargs.pop('lookup_fields', self.lookup_fields)
#         super(ParameterisedHyperlinkedIdentityField, self).__init__(*args, **kwargs)
#
#     def get_url(self, obj, view_name, request, format):
#         """
#         Given an object, return the URL that hyperlinks to the object.
#
#         May raise a `NoReverseMatch` if the `view_name` and `lookup_field`
#         attributes are not configured to correctly match the URL conf.
#         """
#         kwargs = {}
#         for model_field, url_param in self.lookup_fields:
#             attr = obj
#             for field in model_field.split('.'):
#                 attr = getattr(attr,field)
#             kwargs[url_param] = attr
#
#         try:
#             return reverse(view_name, kwargs=kwargs, request=request, format=format)
#         except NoReverseMatch:
#             pass
#
#         raise NoReverseMatch()


class DocumentationSerializer(serializers.HyperlinkedModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name="documentation:sami-docs-detail", lookup_field='slug')
    created = serializers.DateTimeField(format="%Y-%m-%d, %H:%M:%S", read_only=True)
    updated = serializers.DateTimeField(format="%Y-%m-%d, %H:%M:%S", read_only=True)
    title = serializers.CharField(default='My Download', max_length=100, style={'placeholder': 'My Download'})
    content = serializers.CharField(max_length=100000, required=True)
    slug = serializers.SlugField(max_length=20, required=True)

    class Meta:
        model = documentation.models.Documentation
        fields = ('url', 'created', 'updated', 'title', 'content', 'slug')
        lookup_field = 'slug'
        extra_kwargs = {
            'url': {'lookup_field': 'slug'}
        }
        unique = {'slug'}
