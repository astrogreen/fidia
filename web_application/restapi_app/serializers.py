import fidia

from fidia.traits.utilities import TraitProperty
from fidia.traits.base_traits import Trait

from rest_framework import serializers, mixins
from .models import (
    Query
)
from .fields import AstroObjectAbsoluteURLField
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


# ASVO SAMI DR - - - - - - - -    - - -  -   -   -   -   -   -   -   -   -

def get_and_update_depth_limit(kwargs):
    depth_limit = kwargs.pop('depth_limit', -1)
    if isinstance(depth_limit, int):
        if depth_limit > 0:
            depth_limit -= 1
        else:
            depth_limit = 0
    return depth_limit


def get_trait_type_to_serializer_field(traitproperty_type, serializer_type):
    """
    Handles the mapping between FIDIA trait property types
    and DRF serializer types.

    :param traitproperty_type: string
    :return: field type
    """
    # TODO map between FIDIA properties and DRF serializer fields
    # AstroObjectTraitPropertySerializer
    if serializer_type == "source":
        if traitproperty_type == 'ndarray':
            field = serializers.ListField(required=False, source="*")
        elif traitproperty_type == 'float':
            field = serializers.FloatField(required=False, source="*")
        else:
            field = serializers.CharField(max_length=100, required=False, source="*")
        return field

    elif serializer_type == "flat":
        if traitproperty_type == 'float.ndarray' or traitproperty_type == "float.array":
            field = serializers.ListField(required=False)
        elif traitproperty_type == 'float':
            field = serializers.FloatField(required=False)
        else:
            field = serializers.CharField(max_length=100, required=False)
        return field



class AstroObjectTraitPropertySerializer(serializers.Serializer):

    def __init__(self, *args, **kwargs):
        depth_limit = get_and_update_depth_limit(kwargs)
        super().__init__(*args, **kwargs)

        # construct a meaningful key (the current traitproperty in question)
        self.traitproperty_name = self.context['request'].parser_context['kwargs']['traitproperty_pk']

        # define serializer type by instance type
        traitproperty_type = type(self.instance).__name__

        self.fields[self.traitproperty_name] = get_trait_type_to_serializer_field(traitproperty_type, serializer_type="source")



class AstroObjectTraitSerializer(serializers.Serializer):
    def __init__(self, *args, **kwargs):
        depth_limit = get_and_update_depth_limit(kwargs)
        super().__init__(*args, **kwargs)

        trait = self.instance
        assert isinstance(trait, Trait)

        for trait_property in trait._trait_properties():
            # define serializer type by instance type
            traitproperty_type = getattr(trait_property, 'type')

            print(traitproperty_type)
            self.fields[trait_property.name] = get_trait_type_to_serializer_field(traitproperty_type, serializer_type="flat")



class AstroObjectSerializer(serializers.Serializer):
    asvo_id = serializers.SerializerMethodField()

    def get_asvo_id(self,obj):
        return '0000001'

    def __init__(self, *args, **kwargs):
        depth_limit = get_and_update_depth_limit(kwargs)
        super().__init__(*args, **kwargs)

        astro_object = self.instance
        assert isinstance(astro_object, fidia.AstronomicalObject)
        for trait in astro_object:
            depth_limit = 1
            trait_key = trait
            if depth_limit == 0:
                # No details to be displayed below this level
                self.fields[str(trait_key)] = serializers.CharField()
            else:
                # Recurse displaying details at lower level
                self.fields[str(trait_key)] = \
                    AstroObjectTraitSerializer(instance=astro_object[trait_key], depth_limit=depth_limit)

    # object = serializers.CharField(max_length=100, required=False, source="*")



class SampleSerializer(serializers.Serializer):
    def __init__(self, *args, **kwargs):
        depth_limit = get_and_update_depth_limit(kwargs)
        super().__init__(*args, **kwargs)

        sample = self.instance
        assert isinstance(sample, fidia.Sample), \
            "SampleSerializer must have an instance of fidia.Sample, " +\
            "not '%s': try SampleSerializer(instance=sample)" % sample

        for astro_object in sample:
            if depth_limit == 0:
                # No details to be displayed below this level
                self.fields[astro_object] = serializers.CharField()
            else:
                # Recurse displaying details at lower level
                self.fields[astro_object] = AstroObjectSerializer(instance=sample[astro_object], depth_limit=depth_limit)



# class TraitPropertySerializer(serializers.Serializer):
#
#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#
#         trait_property = self.instance
#         assert isinstance(trait_property, TraitProperty)
#
#         value = serializers.CharField(source="*")

# TRAIT_SERIALIZER_CACHE = dict()

# class SimpleTraitSerializer(serializers.Serializer):
#     """Serializer which simply returns the string representation of the Trait"""
#     trait_repr = serializers.CharField(source="*")
#
# def get_serializer_for_trait(self, trait):
#     return SimpleTraitSerializer
#
# class AstroOjbectSerializer(serializers.Serializer):
#
#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#
#         astro_object = self.instance
#         assert isinstance(astro_object, fidia.AstronomicalObject)
#
#         # Iterate over the AstroObject keys (which are keys to traits)
#         for key in astro_object.keys():
#             serializer = get_serializer_for_trait(astro_object[key])
#             self.fields[key] = serializer(required=False)


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
        view_name = 'browse-detail'
        return reverse(view_name, kwargs=url_kwargs)

    name = serializers.SerializerMethodField()
    url = serializers.SerializerMethodField()


class SOVRetrieveObjectSerializer(serializers.Serializer):
    """
    return object name

    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        sample = self.instance
        print(sample)
        for trait in sample:
            print(trait)
            # self.fields[trait] = serializers.CharField()

        # self.fields['velocity_map'] = AstroObjectTraitSerializer

    def get_name(self, obj):
        return obj._identifier

    name = serializers.SerializerMethodField()

    # for trait in obj:
    #     print(trait)

    # for astro_object in sample:
    #     url = get_url(self, view_name="galaxy-list", astro_object=astro_object)
    #     self.fields[astro_object] = AstroObjectAbsoluteURLField(astro_object)
