from rest_framework import serializers, mixins
from restapi_app.models import (
    Query,
    GAMAPublic,
    Survey, SurveyMetaData,
    ReleaseType,
    Catalogue, CatalogueGroup,
    Image,
    Spectrum,
)
from . import AstroObject
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
class AstroObjectSerializer(serializers.Serializer):
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




# def manufacture_trait_serializer(trait):
#
#     class TraitSerializer(serializers.Serializer):
#         id = serializers.IntegerField(read_only=True)
#     # pass
#
#     for tp in trait._trait_properties():
#         if tp.type == "float":
#             print("Creating a float")
#             setattr(TraitSerializer, tp.name, serializers.FloatField(required=False))
#         if tp.type == "string":
#             print("Creating a string")
#             setattr(TraitSerializer, tp.name, serializers.CharField(required=False))
#
#     return TraitSerializer


def manufacture_trait_serializer(trait):
 
    class TraitSerializer(serializers.Serializer):
        redshift = serializers.CharField(required=False, max_length=100, read_only=True)
        line_map = serializers.CharField(required=False, max_length=100, read_only=True)

        # id = serializers.IntegerField(read_only=True)
        # asvoid = serializers.CharField(read_only=True, max_length=100)

        def __init__(self, *args, **kwargs):
            super(TraitSerializer,self).__init__(*args, **kwargs)

            # for tp in trait._trait_properties():
            #     print('--TraitProperties')
            #     print(tp.name, tp.type)
            #     if tp.type == "float":
            #         print("Creating a float")
            #         self.fields[tp.name] = serializers.FloatField(required=False, read_only=True)
            #         # setattr(TraitSerializer, tp.name, serializers.FloatField(required=False))
            #     if tp.type == "string":
            #         print("Creating a string")
            #         self.fields[tp.name] = serializers.CharField(required=False, max_length=100, read_only=True)
            #         # setattr(TraitSerializer, tp.name, serializers.CharField(required=False))
            #     if tp.type == 'float.array':
            #         print(tp)

    return TraitSerializer


class TraitSerializer(serializers.Serializer):
        value = serializers.CharField(required=False, max_length=100, read_only=True)
        #description etc etc
        #happy properties

        # line_map = serializers.CharField(required=False, max_length=100, read_only=True)

def manufacture_galaxy_serializer_for_archive(archive):

    class GalaxySerializer(serializers.Serializer):

        def __init__(self, *args, **kwargs):
            super(GalaxySerializer,self).__init__(*args, **kwargs)

            # Get the schema for the galaxies.
            #
            # {'line_map': {'value': 'float.ndarray', 'variance': 'float.ndarray'},
            # 'redshift': {'value': 'float'},
            # 'spectral_map': {'extra_value': 'float',
            #    'galaxy_name': 'string',
            #    'value': 'float.array',
            #    'variance': 'float.array'},
            # 'velocity_map': {'value': 'float.ndarray', 'variance': 'float.ndarray'}}
            #
            schema = archive.schema()

            for trait in schema:
                if trait != 'spectral_map':
                    print('Trait: ',trait)

                    # self.fields[trait] = manufacture_trait_serializer(trait)
                    # self.fields[trait] = serializers.CharField(required=False, read_only=True)
                    self.fields[trait] = TraitSerializer(required=False)

    return GalaxySerializer