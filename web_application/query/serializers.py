import logging
import json
from django.core.mail import send_mail
import fidia, collections

from fidia.traits import Trait, TraitProperty

from rest_framework import serializers, mixins, status

import query.models
from restapi_app.fields import AbsoluteURLField
from restapi_app.exceptions import Conflict, CustomValidation
from django.contrib.auth.models import User
from rest_framework.reverse import reverse


"""
Serializers:

    Serializing and deserializing the query instances into json, csv representations.

A Serializer class is similar to a form class, and can include similar
validation flags such as required, max_length etc.

The field flags also control how the serializer should be displayed
e.g., when rendering to HTML. This is useful for controlling how the
browsable API should be displayed.

HyperlinkedModelSerializer sub-classes ModelSerializer and uses hyperlinked relationships
instead of primary key relationships.

"""

log = logging.getLogger(__name__)


class QuerySerializer(serializers.HyperlinkedModelSerializer):
    """

    """
    created = serializers.DateTimeField(format="%Y-%m-%d, %H:%M:%S", read_only=True)
    updated = serializers.DateTimeField(format="%Y-%m-%d, %H:%M:%S", read_only=True)
    owner = serializers.ReadOnlyField(source='owner.username')

    # queryBuilderState = serializers.JSONField(label='QB State', allow_null=True, required=False)
    # results = serializers.JSONField(label='Result', required=False, default="{}", read_only=True)

    SQL = serializers.CharField(required=True, allow_blank=False, allow_null=False, style={'base_template': 'textarea.html'})
    title = serializers.CharField(default='My Query', max_length=100, required=False)
    isCompleted = serializers.BooleanField(default=False, read_only=True)

    truncatedResult = serializers.SerializerMethodField()

    def get_truncatedResult(self, obj):
        print(self.context['request'].accepted_media_type)
        return "test"

    class Meta:
        model = query.models.Query
        fields = ('created', 'updated', 'owner', 'queryBuilderState', 'results', 'title', 'SQL', 'url', 'isCompleted', 'id', 'truncatedResult')
        extra_kwargs = {'results': {'required': False}, "queryBuilderState": {"required": False},
                        "title": {"required": False}}



        # # - - - - QUERY - - - -
# class QuerySerializerCreateUpdate(serializers.HyperlinkedModelSerializer):
#     """
#     Create/Update and return a new/existing object instance, given the validated data
#
#     ModelSerializer creates serializer classes (from model) with an automatically
#     determined set of fields and simple implementations of CRUD methods.
#
#     NOTE: JSONField...
#
#     """
#     owner = serializers.ReadOnlyField(source='owner.username')
#     queryResults = serializers.JSONField(required=False, label='Result')
#     title = serializers.CharField(default='My Query', max_length=100)
#     SQL = serializers.CharField(required=True, allow_blank=False, allow_null=False,
#                                 style={'base_template': 'textarea.html'})
#     created = serializers.DateTimeField(format="%Y-%m-%d, %H:%M:%S", read_only=True)
#     flag = serializers.SerializerMethodField()
#
#     def get_flag(self, obj):
#         return ''
#
#     class Meta:
#         model = query.models.Query
#         fields = ('title', 'SQL', 'owner', 'url', 'queryResults', 'flag', 'created')
#
#
# class QuerySerializerList(serializers.HyperlinkedModelSerializer):
#     """
#     Does not display the queryResult field in the list view (no need, extra overhead).
#
#     """
#     owner = serializers.ReadOnlyField(source='owner.username')
#     updated = serializers.DateTimeField(required=True, format="%Y-%m-%d, %H:%M:%S")
#     SQL = serializers.CharField(required=True, allow_blank=False, allow_null=False,
#                                 style={'base_template': 'textarea.html'}, label="SQL")
#
#     class Meta:
#         model = query.models.Query
#         fields = ('title', 'SQL', 'owner', 'url', 'updated')
#         extra_kwargs = {
#             "updated": {
#                 "read_only": True,
#             },
#         }
#
#
# class QuerySerializerRetrieve(serializers.HyperlinkedModelSerializer):
#     """
#     List an existing object instance, given the validated data
#
#     ModelSerializer creates serializer classes (from model) with an automatically
#     determined set of fields and simple implementations of CRUD methods.
#
#     """
#     owner = serializers.ReadOnlyField(source='owner.username')
#     queryResults = serializers.JSONField(required=False, label='Result')
#     updated = serializers.DateTimeField(required=True, format="%Y-%m-%d, %H:%M:%S")
#     flag = serializers.SerializerMethodField()
#     id = serializers.IntegerField(label='ID', read_only=True)
#
#     def get_flag(self, obj):
#         return ''
#
#     class Meta:
#         model = query.models.Query
#         fields = ('title', 'SQL', 'owner', 'url', 'queryResults', 'updated', 'flag', 'id')
#         extra_kwargs = {
#             "queryResults": {
#                 "read_only": True,
#             },
#             "updated": {
#                 "read_only": True,
#             },
#         }