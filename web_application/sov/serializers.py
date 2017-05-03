import logging
import json, os

from rest_framework import serializers, mixins, status
from rest_framework.reverse import reverse

from asvo.fidia_samples_archives import sami_dr1_sample, sami_dr1_archive as ar

import fidia, collections
from fidia.traits import Trait, TraitProperty
from fidia import traits
from fidia.descriptions import DescriptionsMixin

import sov.mixins

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)
os.environ['PYPANDOC_PANDOC'] = '/usr/local/bin/pandoc'

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


class AstroObjectListSerializer(serializers.Serializer):
    pass


class DocumentationHTMLField(serializers.Field):
    """Serializer for the FIDIA documentation for an object as HTML."""

    def get_attribute(self, instance):
        # type: (DescriptionsMixin) -> DescriptionsMixin
        assert isinstance(instance, DescriptionsMixin)
        return instance

    def to_representation(self, obj):
        # type: (DescriptionsMixin) -> str
        return obj.get_documentation(format='html')


class RootSerializer(serializers.Serializer):
    """ Serializer for the Data Browser Root. Lists all surveys available from FIDIA. """

    def get_surveys(self, obj):
        return self.context['surveys']

    surveys = serializers.SerializerMethodField()


class SurveySerializer(sov.mixins.SurveyAttributesMixin):
    """ Serializer for the Data Browser Root. Lists survey's available astronomical objects. """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        survey = self.instance
        assert isinstance(survey, fidia.Sample), \
            "SurveySerializer must have an instance of fidia.Sample, " + \
            "not '%s': try SurveySerializer(instance=sample)" % survey

        self.astro_objects = {}
        for astro_object in survey:
            url_kwargs = {
                'astroobject_pk': str(astro_object),
                'survey_pk': self.context['survey']
            }
            url = reverse("sov:astroobject-list", kwargs=url_kwargs)
            self.astro_objects[astro_object] = url

    def get_astro_objects(self, obj):
        return self.astro_objects

    astro_objects = serializers.SerializerMethodField()


class DownloadSerializer(serializers.Serializer):
    """ Hidden download field on form for post data """
    download = serializers.CharField(default='None', max_length=10000)


class AstroObjectSerializer(serializers.Serializer):
    """ Returns list of available traits. """

    # def get_traits(self, obj):
    #     return self.context['traits']

    def get_catalog_traits(self, obj):
        return self.context['catalog_traits']

    def get_non_catalog_traits(self, obj):
        return self.context['non_catalog_traits']

    def get_position(self, obj):
        return self.context['position']

    def get_catalogs(self, obj):
        # each catalog should carry its group info as sometimes appears detatched from
        # a parent group object
        return [{'name': 'overview_catalog',
                 'data': self.context['overview_catalog'],
                 'pretty_name': 'Overview Catalog',
                 'group': 'summary',
                 'group_pretty_name': 'Summary',
                 'group_info': 'Information about the group/DMI'
                 }]

    # traits = serializers.SerializerMethodField()
    position = serializers.SerializerMethodField()
    catalog_traits = serializers.SerializerMethodField()
    non_catalog_traits = serializers.SerializerMethodField()
    catalogs = serializers.SerializerMethodField()


class TraitSerializer(serializers.Serializer):
    """Serializer for the Trait level of the Data Browser"""

    def __init__(self, *args, **kwargs):
        depth_limit = get_and_update_depth_limit(kwargs)

        log.debug("depth_limit: %s", depth_limit)
        super().__init__(*args, **kwargs)

        trait = self.instance
        assert isinstance(trait, Trait)

        log.debug("Serializing trait '%s'", trait.trait_name)

        log.debug("Adding Sub-traits")
        # define serializer type by instance type

        for sub_trait in trait.get_all_subtraits():
            log.debug("Recursing on subtrait '%s'", sub_trait.trait_name)
            self.fields[sub_trait.trait_name] = TraitSerializer(instance=sub_trait,
                                                                context={
                                                                    'request': self.context['request'],
                                                                }, many=False)

        log.debug("Adding Trait properties")

        for trait_property in trait.trait_properties():

            # Recurse into trait properties
            if 'array' in trait_property.type:
                # TraitProperty is an array, so display a URL for it's value
                self.fields[trait_property.name] = TraitPropertySerializer(
                    instance=trait_property, depth_limit=depth_limit, data_display='url')
            else:
                # TraitProperty is not an array so we want it's actual value returned.
                self.fields[trait_property.name] = TraitPropertySerializer(
                    instance=trait_property, depth_limit=depth_limit, data_display='value')

    description = serializers.SerializerMethodField()
    pretty_name = serializers.SerializerMethodField()
    url = serializers.SerializerMethodField()
    name = serializers.SerializerMethodField()
    units = serializers.SerializerMethodField()
    export_formats = serializers.SerializerMethodField()

    def get_description(self, trait):
        return trait.get_description()

    def get_pretty_name(self, trait):
        return trait.get_pretty_name()

    def get_name(self, trait):
        return trait.trait_name

    def get_url(self, trait):
        """Return URL for current instance (subtrait/tp or tp) - will use in testing """
        # Need to inject the sub-trait url, so this probably needs getting by
        # traversing up the parent tree, though this may not be the best method
        # if has attr (trait) has attr (trait) - prepend
        _url = self.context['trait_url']

        subtrait_str = ""
        # if self._parent_trait is None:
        if hasattr(trait, '_parent_trait'):
            if hasattr(trait._parent_trait, '_parent_trait'):
                subtrait_str = str(trait.trait_name) + '/'

        _url += subtrait_str

        return _url

    def get_units(self, trait):
        return trait.get_formatted_units()

    def get_export_formats(self,trait):
        return trait.get_available_export_formats()

    def get_attribute(self, instance):
        """
        Given the *outgoing* object instance, return the primitive value
        that should be used for this field.
        """
        try:
            # return self.instance

            if isinstance(instance, Trait):
                # Use sub-trait retrieval logic:
                return instance[self.source_attrs[0]]
            else:
                # Use TraitProperty retrieval logic:
                return getattr(instance, self.source_attrs[0])

                # return serializers.get_attribute(instance, self.source_attrs)
        except (KeyError, AttributeError) as exc:
            if not self.required and self.default is serializers.empty:
                raise serializers.SkipField()
            msg = (
                'Got {exc_type} when attempting to get a value for field '
                '`{field}` on serializer `{serializer}`.\nThe serializer '
                'field might be named incorrectly and not match '
                'any attribute or key on the `{instance}` instance.\n'
                'Original exception text was: {exc}.'.format(
                    exc_type=type(exc).__name__,
                    field=self.field_name,
                    serializer=self.parent.__class__.__name__,
                    instance=instance.__class__.__name__,
                    exc=exc
                )
            )
            raise type(exc)(msg)


class TraitPropertySerializer(serializers.Serializer):
    """
    Trait Properties have the following:

        Properties:
            name, type, value

        Methods:
             get_short_name
             get_pretty_name
             get_description
        (these are the 'standard' description fields, see fidia/descriptions.py)
    """

    def __init__(self, *args, **kwargs):
        depth_limit = get_and_update_depth_limit(kwargs)
        data_display = kwargs.pop('data_display', 'value')

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

    def get_value(self, trait_property):
        return self.get_url(trait_property)

    def get_url(self, trait_property):
        """Return URL for current instance (subtrait/tp or tp)"""
        # Need to inject the sub-trait url, so this probably needs getting by
        # traversing up the parent tree, though this may not be the best method
        # if has attr (trait) has attr (trait) - prepend

        _url = self.context['trait_url']

        subtrait_str = ""
        traitproperty_str = ""

        if hasattr(trait_property, '_trait'):
            traitproperty_str = getattr(trait_property, 'name') + '/'

        if hasattr(trait_property, '_trait'):
            if hasattr(trait_property._trait, '_parent_trait'):
                if hasattr(trait_property._trait._parent_trait, '_parent_trait'):
                    subtrait_str = str(trait_property._trait.trait_name) + '/'

        _url += subtrait_str + traitproperty_str

        return _url

    short_name = serializers.SerializerMethodField()
    pretty_name = serializers.SerializerMethodField()
    description = serializers.SerializerMethodField()
    url = serializers.SerializerMethodField()
