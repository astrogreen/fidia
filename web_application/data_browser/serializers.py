import logging
import json

from rest_framework import serializers, mixins, status
from rest_framework.reverse import reverse

from restapi_app.fields import AbsoluteURLField

import fidia, collections
from fidia.traits.utilities import TraitProperty
from fidia.traits.base_traits import Trait
from fidia.descriptions import DescriptionsMixin

log = logging.getLogger(__name__)


def get_and_update_depth_limit(kwargs):
    depth_limit = kwargs.pop('depth_limit', -1)
    if isinstance(depth_limit, int):
        if depth_limit > 0:
            depth_limit -= 1
        else:
            depth_limit = 0

    trait_pk = kwargs.pop('trait_pk', -1)
    if trait_pk == 'spectral_cube':
        depth_limit = 0
    return depth_limit


class DocumentationHTMLField(serializers.Field):
    """Serializer for the FIDIA documentation for an object as HTML."""

    def get_attribute(self, instance):
        # type: (DescriptionsMixin) -> DescriptionsMixin
        assert isinstance(instance, DescriptionsMixin)
        return instance

    def to_representation(self, obj):
        # type: (DescriptionsMixin) -> str
        return obj.get_documentation(format='html')


class DataBrowserSerializer(serializers.Serializer):

    def get_samples(self, obj):
        print(self.context['samples'])
        return self.context['samples']

    samples = serializers.SerializerMethodField()


class SampleSerializer(serializers.Serializer):

    def __init__(self, *args, **kwargs):
        depth_limit = get_and_update_depth_limit(kwargs)
        super().__init__(*args, **kwargs)

        sample = self.instance
        assert isinstance(sample, fidia.Sample), \
            "SampleSerializer must have an instance of fidia.Sample, " +\
            "not '%s': try SampleSerializer(instance=sample)" % sample

        # self.fields['astro_objects'] = serializers.DictField(child=serializers.CharField())
        self.astro_objects = {}
        for astro_object in sample:
            url_kwargs = {
                    'astroobject_pk': str(astro_object),
                    'sample_pk': self.context['sample']
                }
            url = reverse("data_browser:astroobject-list", kwargs=url_kwargs, request=self.context['request'])

            # self.fields[astro_object] = AbsoluteURLField(url=url, required=False)
            self.astro_objects[astro_object] = url
            # # Recurse displaying details at lower level (check depth_limit > 0)
            # self.fields[astro_object] = AstroObjectSerializer(instance=sample[astro_object], depth_limit=depth_limit)

    def get_astro_objects(self, obj):
        return self.astro_objects

    def get_sample(self, obj):
        return self.context['sample']

    sample = serializers.SerializerMethodField()
    astro_objects = serializers.SerializerMethodField()


class AstroObjectSerializer(serializers.Serializer):

    def __init__(self, *args, **kwargs):
        depth_limit = get_and_update_depth_limit(kwargs)
        super().__init__(*args, **kwargs)

        astro_object = self.instance
        assert isinstance(astro_object, fidia.AstronomicalObject)

        # self.fields['name'] = serializers.CharField(required=False)

        # for trait in astro_object:
        #     depth_limit = 0
        #     trait_key = trait
        #
        #     url_kwargs = {
        #         'sample_pk': self.context['sample'],
        #         'astroobject_pk': astro_object._identifier,
        #         'trait_pk': str(trait_key)
        #     }
        #
        #     url = reverse("data_browser:trait-list", kwargs=url_kwargs)
        #     if depth_limit == 0:
        #         self.fields[str(trait_key)] = AbsoluteURLField(url=url, required=False)
        #         # No details to be displayed below this level
        #     else:
        #         # Recurse displaying details at lower level
        #         self.fields[str(trait_key)] = \
        #             AstroObjectTraitSerializer(instance=astro_object[trait_key], depth_limit=depth_limit)

    def get_sample(self, obj):
        return self.context['sample']

    def get_astroobject(self, obj):
        return self.context['astroobject']

    def get_trait_types(self, obj):
        return self.context['trait_types']

    def get_trait_names(self, obj):
        return self.context['trait_names']

    def get_schema(self, obj):
        return self.context['schema']

    sample = serializers.SerializerMethodField()
    astroobject = serializers.SerializerMethodField()
    trait_types = serializers.SerializerMethodField()
    trait_names = serializers.SerializerMethodField()
    # schema = serializers.SerializerMethodField()



class AstroObjectTraitPropertySerializer(serializers.Serializer):

    # documentation = DocumentationHTMLField()
    # short_description = serializers.CharField(source='get_description')
    # pretty_name = serializers.CharField(source='get_pretty_name')

    def __init__(self, *args, **kwargs):
        depth_limit = get_and_update_depth_limit(kwargs)
        data_display = kwargs.pop('data_display', 'include')
        # data_display = 'include'
        super().__init__(*args, **kwargs)

        trait_property = self.instance
        assert isinstance(trait_property, TraitProperty)

        self.fields['name'] = serializers.CharField(required=False)
        self.fields['type'] = serializers.CharField(required=False)

        # Determine the appropriate serializer for the data
        if 'array' in trait_property.type:
            data_serializer = serializers.ListField(required=False)
        elif trait_property.type == 'float':
            data_serializer = serializers.FloatField(required=False)
        elif trait_property.type == 'int':
            data_serializer = serializers.IntegerField(required=False)
        elif trait_property.type == 'string':
            data_serializer = serializers.CharField(required=False)

        if data_display == 'include':
            self.fields['value'] = data_serializer


class AstroObjectTraitSerializer(serializers.Serializer):

    # documentation = DocumentationHTMLField()
    # short_description = serializers.CharField(source='get_description')
    # pretty_name = serializers.CharField(source='get_pretty_name')


    def __init__(self, *args, **kwargs):
        depth_limit = get_and_update_depth_limit(kwargs)
        log.debug("depth_limit: %s", depth_limit)
        super().__init__(*args, **kwargs)

        trait = self.instance
        assert isinstance(trait, Trait)

        for trait_property in trait.trait_properties():
            # define serializer type by instance type
            traitproperty_type = trait_property.type

            # Decide whether data will be included:
            # Turn this back to always on once visualizers have been sorted out. Currently
            # visualization is handled on a per-case basis in the JS via AJAX

            depth_limit = 0
            # Depth limit needs to be a bit more dynamic. It should tunnel down if not spectral cube :)
            # Need some mapping here.

            if depth_limit > 0:
                # Recurse into trait properties
                self.fields[trait_property.name] = AstroObjectTraitPropertySerializer(
                    instance=trait_property, depth_limit=depth_limit, data_display='include')
            else:
                # Simply show the trait types and descriptions
                self.fields[trait_property.name] = AstroObjectTraitPropertySerializer(
                    instance=trait_property, depth_limit=depth_limit, data_display='exclude')




# class DynamicPropertySerializer(serializers.Serializer):
#     """
#     Serializer to handle all types of data combos.
#
#     /asvo/data/astroobject_pk/trait/trait_property/
#     /asvo/data/astroobject_pk/trait/sub-trait/
#     /asvo/data/astroobject_pk/trait/sub-trait/trait_property/
#     /asvo/data/astroobject_pk/trait/sub-trait/sub-trait2/
#
#     Here, pick serializer based on ST/TP instance type
#     """
#     def __init__(self, *args, **kwargs):
#         depth_limit = get_and_update_depth_limit(kwargs)
#         data_display = kwargs.pop('data_display', 'include')
#         super().__init__(*args, **kwargs)
#
#         dynamic_property = self.instance
#         assert isinstance(dynamic_property, TraitProperty) or isinstance(dynamic_property, SubTrait)
#
#         self.fields['name'] = serializers.CharField(required=False)
#         self.fields['type'] = serializers.CharField(required=False)
#
#         # if sub-trait look for trait_properties?
#         if isinstance(dynamic_property, SubTrait):
#             depth_limit = 0
#             for trait_property in dynamic_property.trait_properties():
#                 # define serializer type by instance type
#                 traitproperty_type = trait_property.type
#
#                 if depth_limit > 0:
#                     # Recurse into trait properties
#                     self.fields[trait_property.name] = AstroObjectTraitPropertySerializer(
#                         instance=trait_property, depth_limit=depth_limit, data_display='include')
#                 else:
#                     # Simply show the trait types and descriptions
#                     self.fields[trait_property.name] = AstroObjectTraitPropertySerializer(
#                         instance=trait_property, depth_limit=depth_limit, data_display='exclude')
#
#         if isinstance(dynamic_property, TraitProperty):
#             # if trait_property look for fields at this level
#             # Determine the appropriate serializer field for the data
#             if 'array' in dynamic_property.type:
#                 data_serializer = serializers.ListField(required=False)
#             elif dynamic_property.type == 'float':
#                 data_serializer = serializers.FloatField(required=False)
#             elif dynamic_property.type == 'int':
#                 data_serializer = serializers.IntegerField(required=False)
#             elif dynamic_property.type == 'string':
#                 data_serializer = serializers.CharField(required=False)
#
#             # Decide if data will be included
#             if data_display == 'include':
#                 self.fields['value'] = data_serializer
