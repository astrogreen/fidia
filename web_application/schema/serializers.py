import logging
import json, os, re

from rest_framework import serializers, mixins, status
from rest_framework.reverse import reverse

from restapi_app.fields import AbsoluteURLField

import fidia, collections
from fidia.traits import Trait, TraitProperty
from fidia import traits
from fidia.descriptions import DescriptionsMixin
from fidia.traits.trait_property import BoundTraitProperty
from fidia.archive.archive import Archive

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)

import data_browser.serializers


class SchemaSerializer(serializers.Serializer):
    def get_surveys(self, obj):
        return self.context['surveys']

    surveys = serializers.SerializerMethodField()


class SurveySerializer(serializers.Serializer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        survey = self.instance
        assert isinstance(survey, Archive), \
            "SurveySerializer must have an instance of fidia.Archive, " + \
            "not '%s': try SampleSerializer(instance=sample)" % survey

    def get_survey(self, obj):
        return self.context['survey']

    def get_schema(self, obj):
        # type: (Archive) -> dict
        schema = obj.full_schema(include_subtraits=True, data_class='all', combine_levels=None, verbosity='descriptions', separate_metadata=True)
        return schema

    def get_schema_catalog(self, obj):
        schema_catalog = obj.full_schema(include_subtraits=True, data_class='catalog', combine_levels=None,
                                 verbosity='descriptions', separate_metadata=True)
        return schema_catalog

    def get_schema_non_catalog(self, obj):
        schema_non_catalog = obj.full_schema(include_subtraits=True, data_class='non-catalog', combine_levels=None,
                                 verbosity='descriptions', separate_metadata=True)
        return schema_non_catalog

    survey = serializers.SerializerMethodField()
    schema = serializers.SerializerMethodField()
    schema_catalog = serializers.SerializerMethodField()
    schema_non_catalog = serializers.SerializerMethodField()


class SampleSerializer(serializers.Serializer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        sample = self.instance
        assert isinstance(sample, fidia.Sample), \
            "SampleSerializer must have an instance of fidia.Sample, " + \
            "not '%s': try SampleSerializer(instance=sample)" % sample

        self.astro_objects = {}
        for astro_object in sample:
            url_kwargs = {
                'astroobject_pk': str(astro_object),
                'sample_pk': self.context['sample']
            }
            url = reverse("schema:astroobject-list", kwargs=url_kwargs)

            # self.fields[astro_object] = AbsoluteURLField(url=url, required=False)
            self.astro_objects[astro_object] = url
            # # Recurse displaying details at lower level (check depth_limit > 0)
            # self.fields[astro_object] = AstroObjectSerializer(instance=sample[astro_object], depth_limit=depth_limit)

    def get_astro_objects(self, obj):
        return self.astro_objects

    def get_sample(self, obj):
        return self.context['sample']

    def get_version(self, obj):
        return '1.0'

    def get_data_release_versions(self, obj):
        return ['1.0']

    def get_documentation(self, obj):
        print(obj)
        return 'None'

    sample = serializers.SerializerMethodField()
    astro_objects = serializers.SerializerMethodField()
    data_release_versions = serializers.SerializerMethodField()
    version = serializers.SerializerMethodField()
    documentation = serializers.SerializerMethodField()


class AstroObjectSerializer(serializers.Serializer):
    def get_sample(self, obj):
        return self.context['sample']

    def get_astroobject(self, obj):
        return self.context['astroobject']

    def get_available_traits(self, obj):
        return self.context['available_traits']

    sample = serializers.SerializerMethodField()
    astroobject = serializers.SerializerMethodField()
    available_traits = serializers.SerializerMethodField()

    #
    #
    # class TraitSerializer(data_browser.serializers.TraitSerializer):
    #     """Schema Trait Serializer subclasses from the Data Browser,
    #     you can turn fields off by unsetting them
    #     """
    #     def __init__(self, *args, **kwargs):
    #
    #         super().__init__(*args, **kwargs)
    #
    #         trait = self.instance
    #         assert isinstance(trait, Trait)
    #
    #         for sub_trait in trait.get_all_subtraits():
    #             self.fields[sub_trait.trait_name] = TraitSerializer(instance=sub_trait,
    #                                                                 context={
    #                                                                     'request': self.context['request'],
    #                                                                     'sample': self.context['sample'],
    #                                                                     'astroobject': self.context['astroobject'],
    #                                                                     'trait': self.context['trait'],
    #                                                                     'trait_key': self.context['trait_key'],
    #                                                                 }, many=False)
    #
    #         # Set the field values to their urls (do not return data)
    #         for trait_property in trait.trait_properties():
    #             if not re.match("^[_]", str(trait_property.name)):
    #                 log.debug("Adding Trait Property '%s'", trait_property.name)
    #                 traitproperty_type = trait_property.type
    #                 self.fields[trait_property.name] = TraitPropertySerializer(
    #                     instance=trait_property, data_display='url')
    #
    #     # sample = serializers.SerializerMethodField()
    #     # astroobject = serializers.SerializerMethodField()
    #     # trait = serializers.SerializerMethodField()
    #     # trait_key = serializers.SerializerMethodField()
    #     # url = serializers.SerializerMethodField()
    #     # branch = serializers.SerializerMethodField()
    #     # version = serializers.SerializerMethodField()
    #     # all_branches_versions = serializers.SerializerMethodField()
    #     # description = serializers.SerializerMethodField()
    #     # pretty_name = serializers.SerializerMethodField()
    #     # documentation = serializers.SerializerMethodField()
