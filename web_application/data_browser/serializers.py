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

    def get_surveys(self, obj):
        return self.context['surveys']

    surveys = serializers.SerializerMethodField()


class SurveySerializer(serializers.Serializer):
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
                'sample_pk': self.context['survey']
            }
            url = reverse("data_browser:astroobject-list", kwargs=url_kwargs)
            self.astro_objects[astro_object] = url

    def get_astro_objects(self, obj):
        return self.astro_objects

    def get_survey(self, obj):
        return self.context['survey']

    def get_data_release(self, obj):
        return 1.0

    survey = serializers.SerializerMethodField()
    astro_objects = serializers.SerializerMethodField()
    data_release = serializers.SerializerMethodField()


class AstroObjectSerializer(serializers.Serializer):
    # def __init__(self, *args, **kwargs):
    #     depth_limit = get_and_update_depth_limit(kwargs)
    #     super().__init__(*args, **kwargs)
    #
    #     astro_object = self.instance
    #     assert isinstance(astro_object, fidia.AstronomicalObject)

    def get_sample(self, obj):
        return self.context['sample']

    def get_astroobject(self, obj):
        return self.context['astroobject']

    def get_available_traits(self, obj):
        return self.context['available_traits']

    def get_data_release(self, obj):
        return 1.0

    sample = serializers.SerializerMethodField()
    astroobject = serializers.SerializerMethodField()
    available_traits = serializers.SerializerMethodField()
    data_release = serializers.SerializerMethodField()

class TraitSerializer(serializers.Serializer):
    """Serializer for the Trait level of the Data Browser"""

    def __init__(self, *args, **kwargs):
        depth_limit = get_and_update_depth_limit(kwargs)
        log.debug("depth_limit: %s", depth_limit)
        super().__init__(*args, **kwargs)

        trait = self.instance
        assert isinstance(trait, Trait)

        log.debug("Serializing trait '%s'", trait.trait_name)

        # print(trait.trait_key)
        # print(trait.branch)
        # print(trait)
        # print(vars(trait))
        # print(trait.trait_type)
        # print(type(trait))
        # print(isinstance(trait, traits.Image))

        # If image type, send 2D values for display

        log.debug("Adding Sub-traits")
        # define serializer type by instance type
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
            # if not re.match("^[_]", str(trait_property.name)):
            #     log.debug("Adding Trait Property '%s'", trait_property.name)
            traitproperty_type = trait_property.type

            # Recurse into trait properties
            if 'array' in traitproperty_type:
                # TraitProperty is an array, so display a URL for it's value
                self.fields[trait_property.name] = TraitPropertySerializer(
                    instance=trait_property, depth_limit=depth_limit, data_display='url')
            else:
                # TraitProperty is not an array so we want it's actual value returned.
                self.fields[trait_property.name] = TraitPropertySerializer(
                    instance=trait_property, depth_limit=depth_limit, data_display='value')

    def get_branch(self, trait):
        if trait.branch == None:
            return 'None'
        else:
            return trait.branch

    def get_version(self, trait):
        return trait.version

    def get_all_branches_versions(self, trait):
        b_v_arr = []
        branches={}
        url_kwargs = {
            'astroobject_pk': self.context['astroobject'],
            'sample_pk': self.context['sample']
        }
        # url = reverse("data_browser:astroobject-list", kwargs=url_kwargs, request=self.context['request'])
        # removing request also removes the protocol etc.
        url = reverse("data_browser:astroobject-list", kwargs=url_kwargs)

        # trait.branches_versions.get_pretty_name(branch_name)

        for i in trait.get_all_branches_versions():
            # if i.branch != None:

            branches[str(i.branch)] = {
                "pretty_name":"tbd",
                # "pretty_name":trait.branches_versions.get_pretty_name(str(i.branch)),
                # "description":trait.branches_versions.get_description(str(i.branch)),
                "description":"",
                "versions":i.version
            }


            # Construct URL
            this_url = url + str(i.trait_name) + ':' + str(i.branch)

            # If already in array, append a version to that branch
            for j in b_v_arr:
                if j['branch'] == str(i.branch):
                    j['versions'].append(str.i.version)
            # Else add new branch
            b_v_arr.append({"branch": str(i.branch), "url": this_url,
                            "versions": [str(i.version)]})
        # print(branches)
        # print(b_v_arr)
        return b_v_arr

    def get_description(self, trait):
        return trait.get_description()

    def get_pretty_name(self, trait):
        return trait.get_pretty_name()

    def get_documentation(self, trait):
        # If API - return pre-formatted html, and replace $ with $$ for MathJax

        if self.context['request'].accepted_renderer.format == 'api' or 'html':
            if trait.get_documentation() is not None:
                # return trait.get_documentation('html').replace("$", "$$")
                return trait.get_documentation('html')
            else:
                return trait.get_documentation('html')
        else:
            return trait.get_documentation()

    def get_data_release(self, obj):
        return '1.0'

    def get_sample(self, obj):
        return self.context['sample']

    def get_astroobject(self, obj):
        return self.context['astroobject']

    def get_trait(self, obj):
        return self.context['trait']

    def get_trait_key(self, obj):
        return self.context['trait_key']

    def get_trait_key_array(self, trait):
        return trait.trait_key

    def get_url(self, trait):
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

        if hasattr(trait, '_parent_trait'):
            if hasattr(trait._parent_trait, '_parent_trait'):
                subtrait_str = str(trait.trait_key) + '/'

        _url += subtrait_str

        return _url


    branch = serializers.SerializerMethodField()
    version = serializers.SerializerMethodField()
    all_branches_versions = serializers.SerializerMethodField()
    description = serializers.SerializerMethodField()
    pretty_name = serializers.SerializerMethodField()
    documentation = serializers.SerializerMethodField()

    data_release = serializers.SerializerMethodField()
    sample = serializers.SerializerMethodField()
    astroobject = serializers.SerializerMethodField()
    trait = serializers.SerializerMethodField()
    trait_key = serializers.SerializerMethodField()
    trait_key_array = serializers.SerializerMethodField()
    url = serializers.SerializerMethodField()

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
             get_documentation
        (these are the 'standard' description fields, see fidia/descriptions.py)
    """

    def __init__(self, *args, **kwargs):
        depth_limit = get_and_update_depth_limit(kwargs)
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
        # If API - return pre-formatted html, and replace $ with $$ for MathJax
        if self.context['request'].accepted_renderer.format == 'api' or 'html':
            if trait_property.get_documentation() is not None:
                # return trait_property.get_documentation('html').replace("$", "$$")
                return trait_property.get_documentation('html')
            else:
                return trait_property.get_documentation('html')
        else:
            return trait_property.get_documentation()

    # def get_documentation(self, trait_property):
    #     return trait_property.get_documentation()

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
                    subtrait_str = str(trait_property._trait.trait_key) + '/'

        _url += subtrait_str + traitproperty_str

        return _url

    short_name = serializers.SerializerMethodField()
    pretty_name = serializers.SerializerMethodField()
    description = serializers.SerializerMethodField()
    documentation = serializers.SerializerMethodField()
    url = serializers.SerializerMethodField()

    sample = serializers.SerializerMethodField()
    data_release = serializers.SerializerMethodField()

    def get_data_release(self,obj):
        return '1.0'

    def get_sample(self, obj):
        return self.context['sample']

