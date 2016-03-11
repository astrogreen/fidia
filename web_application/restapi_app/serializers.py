import fidia

from fidia.traits.utilities import TraitProperty
from fidia.traits.base_traits import Trait

from rest_framework import serializers, mixins
from .models import (
    Query,
    GAMAPublic,
    Survey,
    ReleaseType,
    Catalogue, CatalogueGroup,
    Image
)
from . import AstroObject
from django.contrib.auth.models import User
from rest_framework_extensions.fields import ResourceUriField
from rest_framework.routers import reverse
from django.conf import settings

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


#SOV
class GAMASerializer(serializers.HyperlinkedModelSerializer):
    InputCatA = serializers.JSONField(required=False, label='InputCatA')
    TilingCat = serializers.JSONField(required=False, label='TilingCat')
    SpecAll = serializers.JSONField(required=False, label='SpecAll')
    SersicCat = serializers.JSONField(required=False, label='SersicCat')
    Spectrum = serializers.ImageField(max_length=None, allow_empty_file=False, use_url=True)

    CatList = serializers.SerializerMethodField()

    def get_CatList(self,obj):
        return GAMAPublic._meta.get_all_field_names()


    class Meta:
        model = GAMAPublic
        fields = ('url','ASVOID', 'InputCatA', 'TilingCat','SpecAll', 'SersicCat', 'Spectrum', 'CatList')


#FULL DATA MODEL
class SurveySerializer(serializers.HyperlinkedModelSerializer):
    releasetype = serializers.HyperlinkedRelatedField(       #the name of this field == related name of FK in model
        many=True,
        read_only=True,
        view_name='releasetype-detail',
        lookup_field='slugField'
    )

    class Meta:
        model = Survey
        fields = ('url', 'title', 'releasetype')
        extra_kwargs={'url':{'lookup_field':'title'}}

class ReleaseTypeSerializer(serializers.HyperlinkedModelSerializer):
    survey = serializers.HyperlinkedRelatedField(
        queryset=Survey.objects.all(),
        view_name='survey-detail',
        label='Survey',
        lookup_field= 'title'
    )

    catalogue = serializers.HyperlinkedRelatedField(
        many=True,
        queryset=Catalogue.objects.all(),
        view_name='catalogue-detail',
        lookup_field='slugField'
    )

    image = serializers.HyperlinkedRelatedField(
        many=True,
        queryset=Image.objects.all(),
        view_name='image-detail',
        lookup_field='slugField'
    )

    class Meta:
        model = ReleaseType
        fields = ('url','slugField',  'survey', 'releaseTeam', 'dataRelease','catalogue', 'image')
        extra_kwargs = {'survey': {'lookup_field': 'title'}, 'url':{'lookup_field':'slugField'}, 'slugField':{'read_only':True}}

class CatalogueGroupSerializer(serializers.HyperlinkedModelSerializer):
    catalogue = serializers.HyperlinkedRelatedField(
        many=True,
        read_only=True,
        view_name='catalogue-detail',
        lookup_field='slugField'
    )

    class Meta:
        model = CatalogueGroup
        fields = ('url', 'group', 'catalogue')
        extra_kwargs = {'url':{'lookup_field':'slugField'}, 'slugField':{'read_only':True}}

class CatalogueSerializer(serializers.HyperlinkedModelSerializer):
    release = serializers.HyperlinkedRelatedField(
        many=True,
        # read_only=True,
        queryset=ReleaseType.objects.all(),
        view_name='releasetype-detail',
        lookup_field='slugField'
    )
    catalogueGroup = serializers.HyperlinkedRelatedField(
        queryset=CatalogueGroup.objects.all(),
        view_name='cataloguegroup-detail',
        lookup_field='slugField'
    )

    class Meta:
        model = Catalogue

        fields = ('url', 'title', 'content', 'meta', 'version', 'updated', 'release', 'catalogueGroup')
        extra_kwargs = {'url':{'lookup_field':'slugField'}, 'slugField':{'read_only':True}}

class ImageSerializer(serializers.HyperlinkedModelSerializer):
    release = serializers.HyperlinkedRelatedField(
        many=True,
        queryset=ReleaseType.objects.all(),
        view_name='releasetype-detail',
        lookup_field='slugField'
    )

    class Meta:
        model = Image

        fields = ('url', 'title', 'content', 'meta', 'version', 'updated', 'release')
        extra_kwargs = {'url':{'lookup_field':'slugField'}, 'slugField':{'read_only':True}}

class SpectrumSerializer(serializers.HyperlinkedModelSerializer):
    release = serializers.HyperlinkedRelatedField(
        many=True,
        queryset=ReleaseType.objects.all(),
        view_name='releasetype-detail',
        lookup_field='slugField'
    )

    class Meta:
        model = Image

        fields = ('url', 'title', 'content', 'meta', 'version', 'updated', 'release')
        extra_kwargs = {'url':{'lookup_field':'slugField'}, 'slugField':{'read_only':True}}

# NON-MODEL SERIALIZER
class AstroObjectSerializer_old(serializers.Serializer):
    """
    Inherits Serializer as opposed to ModelSerializer and describes the fields
    create() and update() ensure writable

    create() passes validated_data to the AstroObjects initialization
    update() pushes the validated_data values to the given instance. It does
    not assume all fields are available (for patch requests)

    """
    id = serializers.IntegerField(read_only=True)
    asvoid = serializers.CharField(read_only=True, max_length=100)
    gamacataid = serializers.CharField(max_length=100)
    samiid = serializers.CharField(max_length=100, required=False)
    redshift = serializers.FloatField(required=False)
    spectrum = serializers.FileField(required=False)

    def create(self, validated_data):
        return AstroObject(id=None, **validated_data)


    def update(self, instance, validated_data):
        for field, value in validated_data.items():
            setattr(instance, field, value)

        return instance




# - - - - - - - -    - - -  -   -   -   -   -   -   -   -   -

def get_and_update_depth_limit(kwargs):
    depth_limit = kwargs.pop('depth_limit', -1)
    if isinstance(depth_limit, int):
        if depth_limit > 0:
            depth_limit -= 1
        else:
            depth_limit = 0
    return depth_limit

class AstroObjectPropertyTraitSerializer(serializers.Serializer):
    def __init__(self, *args, **kwargs):
        depth_limit = get_and_update_depth_limit(kwargs)
        super().__init__(*args, **kwargs)

        # construct a meaningful key (the current traitproperty in question)
        self.traitproperty_name = self.context['request'].parser_context['kwargs']['traitproperty_pk']
        self.fields[self.traitproperty_name] = serializers.CharField(max_length=100, required=False, source="*")


class AstroObjectTraitSerializer(serializers.Serializer):
    def __init__(self, *args, **kwargs):
        depth_limit = get_and_update_depth_limit(kwargs)
        super().__init__(*args, **kwargs)

        trait = self.instance
        assert isinstance(trait, Trait)

        for trait_property in trait._trait_properties():
            self.fields[trait_property.name] = serializers.CharField(max_length=100, required=False)

        # self.fields['object'] = serializers.CharField(max_length=100, required=False, source="*")


class AstroObjectSerializer(serializers.Serializer):
    asvo_id = serializers.SerializerMethodField()

    def get_asvo_id(self,obj):
        return '0000001'

    def __init__(self, *args, **kwargs):
        depth_limit = get_and_update_depth_limit(kwargs)
        super().__init__(*args, **kwargs)

        astro_object = self.instance
        assert isinstance(astro_object, fidia.AstronomicalObject)
        for trait_key in astro_object:
            print(depth_limit)
            depth_limit = 1
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







# class TraitSerializerFactory:

class TraitPropertySerializer(serializers.Serializer):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        trait_property = self.instance
        assert isinstance(trait_property, TraitProperty)

        value = serializers.CharField(source="*")

TRAIT_SERIALIZER_CACHE = dict()

class SimpleTraitSerializer(serializers.Serializer):
    """Serializer which simply returns the string representation of the Trait"""
    trait_repr = serializers.CharField(source="*")

def get_serializer_for_trait(self, trait):
    return SimpleTraitSerializer

class AstroOjbectSerializer(serializers.Serializer):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        astro_object = self.instance
        assert isinstance(astro_object, fidia.AstronomicalObject)

        # Iterate over the AstroObject keys (which are keys to traits)
        for key in astro_object.keys():
            serializer = get_serializer_for_trait(astro_object[key])
            self.fields[key] = serializer(required=False)

