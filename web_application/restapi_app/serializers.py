import logging

import fidia, collections

from fidia.traits.utilities import TraitProperty
from fidia.traits.base_traits import Trait

from rest_framework import serializers, mixins
from .models import (
    Query
)
from .fields import AbsoluteURLField
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

# QUERYING
class QuerySerializerCreateUpdate(serializers.HyperlinkedModelSerializer):
    """
    Create/Update and return a new/existing object instance, given the validated data

    ModelSerializer creates serializer classes (from model) with an automatically
    determined set of fields and simple implementations of CRUD methods.

    NOTE: JSONField...

    """
    owner = serializers.ReadOnlyField(source='owner.username')
    queryResults = serializers.JSONField(required=False, label='Result')
    title = serializers.CharField(default='My Query', max_length=100)
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
    updated = serializers.DateTimeField(required=True, format="%Y-%m-%d, %H:%M:%S")

    class Meta:
        model = Query
        fields = ('title', 'SQL', 'owner', 'url', 'queryResults', 'updated')
        extra_kwargs = {
            "queryResults": {
                "read_only": True,
            },
            "updated": {
                "read_only": True,
            },
        }


class CreateUserSerializer(serializers.ModelSerializer):

    def validate(self, data):
        """
        Checks to be sure that the received password and confirm_password
        fields are exactly the same
        """
        if data['password'] != data.pop('confirm_password'):
            raise serializers.ValidationError("Passwords do not match")
        return data

    password = serializers.CharField(
          write_only=True,
    )
    confirm_password = serializers.CharField(allow_blank=False, write_only=True, required=True)

    # def validate(self, data):
    #     if data.get('password') != data.get('confirm_password'):
    #         raise serializers.ValidationError("Those passwords don't match.")
    #     return data

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'username', 'password', 'confirm_password')




    def create(self, validated_data):
        user = super(CreateUserSerializer, self).create(validated_data)
        if 'password' in validated_data:
            user.set_password(validated_data['password'])
            user.save()
        return user


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


# ASVO SAMI DR - - - - - - - -    - - -  -   -   -   -   -   -   -   -   -

def get_and_update_depth_limit(kwargs):
    depth_limit = kwargs.pop('depth_limit', -1)
    if isinstance(depth_limit, int):
        if depth_limit > 0:
            depth_limit -= 1
        else:
            depth_limit = 0
    return depth_limit


class AstroObjectTraitPropertySerializer(serializers.Serializer):

    def __init__(self, *args, **kwargs):
        depth_limit = get_and_update_depth_limit(kwargs)
        data_display = kwargs.pop('data_display', 'include')
        super().__init__(*args, **kwargs)

        trait_property = self.instance
        assert isinstance(trait_property, TraitProperty)

        # Determine the appropriate serializer for the data
        if 'array' in trait_property.type:
            data_serializer = serializers.ListField(required=False)
        elif trait_property.type == 'float':
            data_serializer = serializers.FloatField(required=False)
        elif trait_property.type == 'int':
            data_serializer = serializers.IntegerField(required=False)
        elif trait_property.type == 'string':
            data_serializer = serializers.CharField(required=False)


        self.fields['name'] = serializers.CharField(required=False)
        self.fields['type'] = serializers.CharField(required=False)
        # Decide whether data will be included:
        if data_display == 'include':
            self.fields['value'] = data_serializer


class AstroObjectTraitSerializer(serializers.Serializer):

    def __init__(self, *args, **kwargs):
        depth_limit = get_and_update_depth_limit(kwargs)
        log.debug("depth_limit: %s", depth_limit)
        super().__init__(*args, **kwargs)

        trait = self.instance
        assert isinstance(trait, Trait)

        for trait_property in trait.trait_properties():
            # define serializer type by instance type
            traitproperty_type = trait_property.type

            if depth_limit > 0:
                # Recurse into trait properties
                self.fields[trait_property.name] = AstroObjectTraitPropertySerializer(
                    instance=trait_property, depth_limit=depth_limit, data_display='include')
            else:
                # Simply show the trait types and descriptions
                self.fields[trait_property.name] = AstroObjectTraitPropertySerializer(
                    instance=trait_property, depth_limit=depth_limit, data_display='exclude')


class AstroObjectSerializer(serializers.Serializer):

    # asvo_id = serializers.SerializerMethodField()
    #
    # def get_asvo_id(self,obj):
    #     return '0000001'

    def __init__(self, *args, **kwargs):
        depth_limit = get_and_update_depth_limit(kwargs)
        super().__init__(*args, **kwargs)

        astro_object = self.instance
        assert isinstance(astro_object, fidia.AstronomicalObject)

        # def get_url(self, view_name, astro_object):
        #     url_kwargs = {
        #         'galaxy_pk': astro_object
        #     }
        #     return reverse(view_name, kwargs=url_kwargs)

        for trait in astro_object:
            depth_limit = 0
            trait_key = trait

            url_kwargs = {
                'galaxy_pk': astro_object._identifier,
                'trait_pk': str(trait_key)
            }

            url = reverse("trait-list", kwargs=url_kwargs)
            if depth_limit == 0:
                self.fields[str(trait_key)] = AbsoluteURLField(url=url, required=False)
                # No details to be displayed below this level
            else:
                # Recurse displaying details at lower level
                self.fields[str(trait_key)] = \
                    AstroObjectTraitSerializer(instance=astro_object[trait_key], depth_limit=depth_limit)

    def get_schema(self, obj):
        return self.context['schema']

    schema = serializers.SerializerMethodField()
    # object = serializers.CharField(max_length=100, required=False, source="*")


class SampleSerializer(serializers.Serializer):
    def __init__(self, *args, **kwargs):
        depth_limit = get_and_update_depth_limit(kwargs)
        super().__init__(*args, **kwargs)

        sample = self.instance
        assert isinstance(sample, fidia.Sample), \
            "SampleSerializer must have an instance of fidia.Sample, " +\
            "not '%s': try SampleSerializer(instance=sample)" % sample
        depth_limit = 0

        for astro_object in sample:
            url_kwargs = {
                    'galaxy_pk': str(astro_object),
                }
            url = reverse("galaxy-list", kwargs=url_kwargs)


            if depth_limit == 0:
                # No details to be displayed below this level
                # self.fields[astro_object] = serializers.CharField()
                self.fields[astro_object] = AbsoluteURLField(url=url, required=False)
            else:
                # Recurse displaying details at lower level
                self.fields[astro_object] = AstroObjectSerializer(instance=sample[astro_object], depth_limit=depth_limit)



# TESTING SOV
class SOVListSurveysSerializer(serializers.Serializer):
    """
    return list available objects in sample

    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        sample = self.instance
        assert isinstance(sample, fidia.Sample), \
            "SampleSerializer must have an instance of fidia.Sample, " +\
            "not '%s': try SampleSerializer(instance=sample)" % sample

    # def get_url(self, view_name, astro_object):
        # url_kwargs = {
        #     'galaxy_pk': astro_object
        # }
        # return reverse(view_name, kwargs=url_kwargs)

    def get_name(self, obj_name):
        return obj_name

    def get_url(self, obj_name):
        url_kwargs = {
            'pk': obj_name
        }
        view_name = 'sov-detail'
        return reverse(view_name, kwargs=url_kwargs)

    name = serializers.SerializerMethodField()
    url = serializers.SerializerMethodField()


class SOVRetrieveObjectSerializer(serializers.Serializer):
    """
    return object name & velocity map only

    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        astro_object = self.instance
        assert isinstance(astro_object, fidia.AstronomicalObject)
        for trait in astro_object:
            trait_key = trait
            if str(trait_key) == "velocity_map" or str(trait_key) == 'line_map-SII6716':
                self.fields[str(trait_key)] = \
                    AstroObjectTraitSerializer(instance=astro_object[trait_key], depth_limit=2)

    def get_samiID(self, obj):
        return obj._identifier

    def get_ra(self, obj):
        return obj['spectral_cube-red'].ra()

    def get_dec(self, obj):
        return obj['spectral_cube-red'].dec()

    samiID = serializers.SerializerMethodField()
    ra = serializers.SerializerMethodField()
    dec = serializers.SerializerMethodField()