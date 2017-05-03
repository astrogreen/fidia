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


class QueryListSerializer(serializers.HyperlinkedModelSerializer):
    """
    List serializer does not include the queryBuilderState or results
    """
    created = serializers.DateTimeField(format="%Y-%m-%d, %H:%M:%S", read_only=True)
    updated = serializers.DateTimeField(format="%Y-%m-%d, %H:%M:%S", read_only=True)
    # owner = serializers.ReadOnlyField(source='owner.username')

    # SQL = serializers.CharField(required=True, allow_blank=False, allow_null=False, style={'base_template': 'textarea.html'})
    title = serializers.CharField(default='My Query', max_length=100, required=False)
    is_completed = serializers.BooleanField(default=False, read_only=True)

    class Meta:
        model = query.models.Query
        fields = ('id', 'title', 'created', 'updated', 'url', 'is_completed')
        extra_kwargs = {'results': {'required': False}, "query_builder_state": {"required": False},
                        "title": {"required": False}}


class QueryRetrieveSerializer(serializers.HyperlinkedModelSerializer):
    """

    """
    created = serializers.DateTimeField(format="%Y-%m-%d, %H:%M:%S", read_only=True)
    updated = serializers.DateTimeField(format="%Y-%m-%d, %H:%M:%S", read_only=True)
    owner = serializers.ReadOnlyField(source='owner.username')

    sql = serializers.CharField(required=True, allow_blank=False, allow_null=False,
                                style={'base_template': 'textarea.html'})
    title = serializers.CharField(default='My Query', max_length=100, required=False)
    is_completed = serializers.BooleanField(default=False, read_only=True)

    results = serializers.SerializerMethodField()

    def get_results(self, obj):
        # Get the top X number of rows from the table_name results table
        # to display to the user on the front end.
        dummy_results = {
            "data": [[559813, 0.3736799955368042, 4, 5, 0.3753318786621094],
                     [144885, 0.08026000112295151, 4, 2, 0.0815441831946373],
                     [507773, 0.1811300069093704, 4, 5, 0.18213008344173431]],
            "columns": [
                {"name": "StellarMasses_CATAID", "type": "integer",
                 "typeSignature": {"rawType": "integer", "arguments": [], "typeArguments": [],
                                   "literalArguments": []}},
                {"name": "StellarMasses_Z", "type": "double",
                 "typeSignature": {"rawType": "double",
                                   "arguments": [],
                                   "typeArguments": [],
                                   "literalArguments": []}},
                {"name": "StellarMasses_nQ", "type": "integer",
                 "typeSignature": {"rawType": "integer", "arguments": [], "typeArguments": [],
                                   "literalArguments": []}},
                {"name": "StellarMasses_SURVEY_CODE", "type": "integer",
                 "typeSignature": {"rawType": "integer", "arguments": [], "typeArguments": [],
                                   "literalArguments": []}},
                {"name": "StellarMasses_Z_TONRY", "type": "double",
                 "typeSignature": {"rawType": "double",
                                   "arguments": [],
                                   "typeArguments": [],
                                   "literalArguments": []}}
            ]}

        # Retrieve the top 2000 rows from the table
        if (obj.is_completed and not obj.is_expired and obj.table_name):
            # TODO write this function get_table(name=obj.table_name, length=2000)
            return dummy_results;
        return None


    class Meta:
        model = query.models.Query
        fields = (
            'created',
            'updated',
            'owner',

            'query_builder_state',
            'title',
            'sql',

            'url',
            'id',

            'is_completed',
            'is_expired',
            'results',
            'table_name',
            'row_count',
            'has_error',
            'error')

        extra_kwargs = {'results': {'required': False}, "query_builder_state": {"required": False},
                        "title": {"required": False}}


class QueryCreateSerializer(serializers.HyperlinkedModelSerializer):
    """
    
    """
    title = serializers.CharField(max_length=100, required=True)
    # queryBuilderState = serializers.JSONField(label='QB State', required=False, default="{}")

    # TODO update DRF as per fix to https://github.com/encode/django-rest-framework/issues/4999
    # JSONField not rendered properly in DRF browsable API HTML form
    sql = serializers.CharField(required=True, label='SQL', allow_blank=False, allow_null=False,
                                style={'base_template': 'textarea.html'})

    class Meta:
        model = query.models.Query
        fields = ('title', 'query_builder_state', 'sql', 'id')

# Testing in django
# class ResultListSerializer(serializers.Serializer):
#     id = serializers.IntegerField()
#     class Meta:
#         fields = ('id')
#
#
# class ResultRetrieveSerializer(serializers.Serializer):
#     def __init__(self, *args, **kwargs):
#         super(ResultRetrieveSerializer, self).__init__(*args, **kwargs)
#         # iterate over dict keys to generate fields on the fly
#         for f in self.instance[0]:
#             self.fields[f] = serializers.CharField()
