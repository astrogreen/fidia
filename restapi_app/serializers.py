from rest_framework import serializers, mixins
from restapi_app.models import Query, Survey, Version, Product
from django.contrib.auth.models import User
from rest_framework_extensions.fields import ResourceUriField

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

class QuerySerializerCreateUpdate(serializers.HyperlinkedModelSerializer):
    """
    Create/Update and return a new/existing object instance, given the validated data

    ModelSerializer creates serializer classes (from model) with an automatically
    determined set of fields and simple implementations of CRUD methods.

    NOTE: JSONField...

    """
    owner = serializers.ReadOnlyField(source='owner.username')
    queryResults = serializers.JSONField(required=False, label='Result')

    class Meta:
        model = Query
        fields = ('title', 'SQL', 'owner', 'url', 'queryResults')


class QuerySerializerList(serializers.HyperlinkedModelSerializer):
    """
    List an existing object instance, given the validated data

    ModelSerializer creates serializer classes (from model) with an automatically
    determined set of fields and simple implementations of CRUD methods.

    NOTE: SerializerMethodField is a read-only field.
    It can be used to add any sort of data to the serialized representation
    of an object. Here, the csv file and url can be generated (from the
    pre-existing sample under queryResults) on the fly

    """
    owner = serializers.ReadOnlyField(source='owner.username')
    queryResults = serializers.JSONField(required=False, label='Result')
    csvButton = serializers.SerializerMethodField(label='CSV Link')

    class Meta:
        model = Query
        fields = ('title', 'SQL', 'owner', 'url', 'queryResults', 'updated', 'csvButton')
        extra_kwargs = {
            "queryResults": {
                "read_only": True,
            },
            "updated": {
                "read_only": True,
            },
        }

    def get_csvButton(self, obj):
        return 'csv_url_string'



class UserSerializer(serializers.HyperlinkedModelSerializer):
    """

    NOTE: many=True flag allows serialization of queryset instead of model instance.
    'query' is a reverse relationship on the User model, and will not be included by
    default in the (Hyperlinked)ModelSerializer class - so an explicit field is added.
    """
    query = serializers.HyperlinkedRelatedField(many=True, view_name='query-detail', read_only=True)

    class Meta:
        model = User
        fields = ('url', 'username', 'query')





class SurveySerializer(serializers.HyperlinkedModelSerializer):
    """
    NOTE:
    """
    version = serializers.HyperlinkedRelatedField(many=True, view_name='version-detail', read_only=True)

    class Meta:
        model = Survey
        # fields = ('url', 'survey')
        fields = ('url', 'survey', 'version')
        # extra_kwargs = {'version': {'view_name': 'version-detail'}}


class VersionSerializer(serializers.HyperlinkedModelSerializer):
    """
    NOTE:
    """
    # survey = SurveySerializer()
    class Meta:
        model = Version
        fields = ('id', 'version', 'survey')
