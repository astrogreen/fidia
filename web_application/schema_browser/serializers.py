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

import sov.serializers


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

    # def get_schema(self, obj):
    #     # type: (Archive) -> dict
    #     schema = obj.full_schema(include_subtraits=True, data_class='all', combine_levels=None,
    #                              verbosity='descriptions', separate_metadata=True)
    #     return schema
    #
    def get_schema_catalog(self, obj):
        schema_catalog = obj.full_schema(include_subtraits=True, data_class='catalog', combine_levels=None,
                                         verbosity='descriptions', separate_metadata=True)

        schema_non_catalog = obj.full_schema(include_subtraits=False, verbosity='simple', data_class='non-catalog',
                                             combine_levels=None, separate_metadata=True)

        # remove non-catalog traits from catalog schema
        for key in schema_non_catalog["trait_types"]:
            if key in schema_catalog["trait_types"]:
                schema_catalog["trait_types"].pop(key)
        return schema_catalog

    def get_schema_non_catalog(self, obj):
        schema_non_catalog = obj.full_schema(include_subtraits=False, data_class='non-catalog', combine_levels=None,
                                             verbosity='descriptions', separate_metadata=True)
        return schema_non_catalog

    survey = serializers.SerializerMethodField()
    # schema = serializers.SerializerMethodField()
    schema_catalog = serializers.SerializerMethodField()
    schema_non_catalog = serializers.SerializerMethodField()


class TraitSerializer(serializers.Serializer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    trait = serializers.SerializerMethodField()

    def get_trait(self, obj):
        return obj


class DynamicSerializer(serializers.Serializer):
    def __init__(self, *args, **kwargs):
        # Instantiate the superclass normally
        super(DynamicSerializer, self).__init__(*args, **kwargs)
        # pop off trait_property field if the type is sub_trait
        if self.context['dynamic_type'] == 'sub_trait':
            self.fields.pop('trait_property')
        else:
            self.fields.pop('sub_trait')

    def get_obj(self, obj):
        return obj

    trait_property = serializers.SerializerMethodField('get_obj')
    sub_trait = serializers.SerializerMethodField('get_obj')
