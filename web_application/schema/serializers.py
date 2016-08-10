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
log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)

import data_browser.serializers


class SchemaSerializer(serializers.Serializer):

    def get_samples(self, obj):
        return self.context['samples']

    samples = serializers.SerializerMethodField()


class SampleSerializer(serializers.Serializer):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        sample = self.instance
        assert isinstance(sample, fidia.Sample), \
            "SampleSerializer must have an instance of fidia.Sample, " +\
            "not '%s': try SampleSerializer(instance=sample)" % sample

        self.astro_objects = {}
        for astro_object in sample:
            url_kwargs = {
                    'astroobject_pk': str(astro_object),
                    'sample_pk': self.context['sample']
                }
            url = reverse("schema:astroobject-list", kwargs=url_kwargs, request=self.context['request'])

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



class TraitSerializer(data_browser.serializers.TraitSerializer):
    """Schema Trait Serializer subclasses from the Data Browser,
    you can turn fields off by setting their value.
    """
    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

        trait = self.instance
        assert isinstance(trait, Trait)

        for sub_trait in trait.get_all_subtraits():

            log.debug("Recursing on subtrait '%s'", sub_trait.trait_name)
            # setattr(self, sub_trait.trait_name, None)

            self.fields[sub_trait.trait_name] = TraitSerializer(instance=sub_trait,
                                                                context={
                                                                    'request': self.context['request'],
                                                                    'sample': self.context['sample'],
                                                                    'astroobject': self.context['astroobject'],
                                                                    'trait': self.context['trait'],
                                                                    'trait_key': self.context['trait_key'],
                                                                }, many=False)

        log.debug("Adding Trait properties")

        for trait_property in trait.trait_properties():
            if not re.match("^[_]", str(trait_property.name)):
                log.debug("Adding Trait Property '%s'", trait_property.name)
                traitproperty_type = trait_property.type

                # Recurse into trait properties
                if 'array' in traitproperty_type:
                    # TraitProperty is an array, so display a URL for it's value
                    self.fields[trait_property.name] = TraitPropertySerializer(
                        instance=trait_property, data_display='url')
                else:
                    # TraitProperty is not an array so we want it's actual value returned.
                    self.fields[trait_property.name] = TraitPropertySerializer(
                        instance=trait_property, data_display='value')

    sample = serializers.SerializerMethodField()
    astroobject = serializers.SerializerMethodField()
    trait = serializers.SerializerMethodField()
    trait_key = serializers.SerializerMethodField()
    url = serializers.SerializerMethodField()
    branch = serializers.SerializerMethodField()
    version = serializers.SerializerMethodField()
    all_branches_versions = serializers.SerializerMethodField()
    description = serializers.SerializerMethodField()
    pretty_name = serializers.SerializerMethodField()
    documentation = serializers.SerializerMethodField()




class TraitPropertySerializer(serializers.Serializer):
    """
    Trait Properties have the following:

        Properties:
            name, type, value

        Methods:
             get_short_name
             get_pretty_name
             get_description
             get_documentation
        (these are the 'standard' description fields, see fidia/descriptions.py)
    """

    def __init__(self, *args, **kwargs):
        # depth_limit = get_and_update_depth_limit(kwargs)
        data_display = kwargs.pop('data_display', 'value')
        # data_display = 'include'
        super().__init__(*args, **kwargs)

        if isinstance(self.instance, TraitProperty):
            trait_property = self.instance

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

            if data_display == 'value':
                self.fields['value'] = data_serializer
            elif data_display == 'url':
                self.fields['value'] = serializers.SerializerMethodField()

    def get_short_name(self, trait_property):
        return trait_property.get_short_name()
    def get_pretty_name(self, trait_property):
        return trait_property.get_pretty_name()
    def get_description(self, trait_property):
        return trait_property.get_description()
    def get_documentation(self, trait_property):
        return trait_property.get_documentation()

    def get_value(self, trait_property):
        return self.get_url(trait_property)

    def get_url(self, trait_property):
        """Return URL for current instance (subtrait/tp or tp)"""
        # Need to inject the sub-trait url, so this probably needs getting by
        # traversing up the parent tree, though this may not be the best method
        # if has attr (trait) has attr (trait) - prepend

        url_kwargs = {
            'astroobject_pk': self.context['astroobject'],
            'sample_pk': self.context['sample'],
            'trait_pk': self.context['trait'],
        }
        _url = reverse("data_browser:trait-list", kwargs=url_kwargs)

        subtrait_str = ""
        traitproperty_str = ""

        if hasattr(trait_property, '_trait'):
            traitproperty_str = getattr(trait_property, 'name') + '/'

        if hasattr(trait_property, '_trait'):
            if hasattr(trait_property._trait, '_parent_trait'):
                if hasattr(trait_property._trait._parent_trait, '_parent_trait'):
                    subtrait_str = str(trait_property._trait.trait_key)+'/'

        _url += subtrait_str + traitproperty_str

        return _url

    short_name = serializers.SerializerMethodField()
    pretty_name = serializers.SerializerMethodField()
    description = serializers.SerializerMethodField()
    documentation = serializers.SerializerMethodField()
    url = serializers.SerializerMethodField()


class AttributeSerializer(serializers.Serializer):
    """
    This will be used if an endpoint is identified as an attribute on an instance of Trait or Trait property,
    rather than either of the latter.
    The call logic for this function will go in the Dynamic ViewSet (once I figure out how to call methods
    dynamically (ie., get_<dynamic_pk> on <trait_pk or <trait_property_pk>
    """
    pass

