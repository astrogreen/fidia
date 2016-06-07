import logging

from rest_framework import serializers, mixins, status
from rest_framework.reverse import reverse

from restapi_app.fields import AbsoluteURLField

import fidia, collections
from fidia.traits.utilities import TraitProperty
from fidia.traits.base_traits import Trait

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


# class DynamicPropertySerializer(serializers.Serializer):
#     """
#     Serializer to handle all types of data combos.
#
#     /asvo/data/galaxy_pk/trait/trait_property/
#     /asvo/data/galaxy_pk/trait/sub-trait/
#     /asvo/data/galaxy_pk/trait/sub-trait/trait_property/
#     /asvo/data/galaxy_pk/trait/sub-trait/sub-trait2/
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


class AstroObjectTraitPropertySerializer(serializers.Serializer):

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


class AstroObjectSerializer(serializers.Serializer):

    def __init__(self, *args, **kwargs):
        depth_limit = get_and_update_depth_limit(kwargs)
        super().__init__(*args, **kwargs)

        astro_object = self.instance
        assert isinstance(astro_object, fidia.AstronomicalObject)

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
