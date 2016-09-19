from io import BytesIO
import logging

from rest_framework import renderers
from rest_framework.exceptions import UnsupportedMediaType

from asvo.fidia_samples_archives import sami_dr1_sample, sami_dr1_archive as ar
from fidia import traits

import restapi_app.renderers

import data_browser.views

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)

CONTEXT = {}

CONTEXT['reserved_keywords'] = ['sample', 'data_release', 'astro_object', 'trait', 'trait_key', 'trait_key_array',
                                'trait_url', 'sub_trait_key',
                                'pretty_name', 'short_name', 'branch', 'version', 'url', 'all_branches_versions',
                                'documentation']


class FITSRenderer(renderers.BaseRenderer):
    media_type = "application/fits"
    format = "fits"
    charset = None

    def render(self, data, accepted_media_type=None, renderer_context=None):
        log.debug("Render response: %s" % renderer_context['response'])
        trait = data.serializer.instance
        if not isinstance(trait, traits.Trait):
            raise UnsupportedMediaType("Renderer doesn't support anything but Traits!")

        byte_file = BytesIO()

        trait.as_fits(byte_file)

        return byte_file.getvalue()


class RootRenderer(restapi_app.renderers.ExtendBrowsableAPIRenderer):
    template = 'data_browser/root/list.html'

    def __repr__(self):
        return 'RootRenderer'


class SampleRenderer(restapi_app.renderers.ExtendBrowsableAPIRenderer):
    template = 'data_browser/survey/list.html'

    def __repr__(self):
        return 'SampleRenderer'


class AstroObjectRenderer(restapi_app.renderers.ExtendBrowsableAPIRenderer):
    template = 'data_browser/astro_object/list.html'

    def __repr__(self):
        return 'AstroObjectRenderer'

    def get_context(self, data, accepted_media_type, renderer_context):
        context = super().get_context(data, accepted_media_type, renderer_context)
        context['traits_to_render'] = {"sami": ['velocity_map', 'sfr_map']}

        return context


class TraitRenderer(restapi_app.renderers.ExtendBrowsableAPIRenderer):
    def __init__(self, sub_trait_list_extended=None, *args, **kwargs):
        # pass
        self.template = 'data_browser/trait/list.html'

    def __repr__(self):
        return 'TraitRenderer'

    def get_context(self, data, accepted_media_type, renderer_context):
        """ Add reserved keys to the context so the template knows not to iterate over these keys, rather,
        they will be explicitly positioned. """

        context = super().get_context(data, accepted_media_type, renderer_context)

        # These are not looped over for the top-level trait view (but appear in the properties panel)
        context['side_bar_explicit_render'] = [ 'description']

        # These will be explicitly rendered for a trait, all else will be iterated over in the side bar
        context['trait_properties'] = ['value']

        context['trait_property_keywords'] = ["short_name", "pretty_name", "description", "url",
                                              "name", "type", "value", ]

        trait = sami_dr1_sample[data['astro_object']][data['trait']]

        context['sub_traits'] = [sub_trait.trait_name for sub_trait in trait.get_all_subtraits()]

        # These are not looped over for the html rendering
        context['reserved_keywords'] = CONTEXT['reserved_keywords'] + \
                                       context['side_bar_explicit_render'] + \
                                       context['trait_properties'] + \
                                       context['sub_traits']
        # Formats
        trait_name_formats = []
        for r in data_browser.views.TraitViewSet.renderer_classes:
            f = str(r.format)
            if f != "api": trait_name_formats.append(f)

        context['formats'] = trait_name_formats

        context['trait_type'] = trait.trait_type

        if isinstance(trait, traits.Map2D):
            context['trait_2D_map'] = True

        # context['short_description'] = renderer_context['view'].short_description
        return context


class SubTraitPropertyRenderer(restapi_app.renderers.ExtendBrowsableAPIRenderer):
    def __repr__(self):
        return 'SubTraitPropertyRenderer'

    def get_context(self, data, accepted_media_type, renderer_context):
        """ Add reserved keys to the context so the template knows not to iterate over these keys, rather,
        they will be explicitly positioned. """

        context = super().get_context(data, accepted_media_type, renderer_context)
        context['sample'] = renderer_context['view'].sample
        context['astro_object'] = renderer_context['view'].astro_object
        context['trait'] = renderer_context['view'].trait
        context['trait_url'] = renderer_context['view'].trait_url
        context['template'] = renderer_context['view'].template

        context['fidia_keys'] = ['sample', 'astro_object', 'trait', 'trait_key', 'trait_key_array', 'sub_trait_key',
                                 'data_release', ]
        context['side_bar_explicit_render'] = ['description']

        context['trait_property_keywords'] = ["short_name", "pretty_name", "description",
                                              "name", "type", "value", ]

        context['reserved_keywords'] = CONTEXT['reserved_keywords'] + ['pretty_name', 'short_name', 'branch', 'version', "url",
                                        'all_branches_versions', 'documentation' ] + \
                                       context['side_bar_explicit_render'] + \
                                       context['fidia_keys']

        context['type'] = renderer_context['view'].type
        context['formats'] = renderer_context['view'].formats
        context['branch'] = renderer_context['view'].branch
        context['version'] = renderer_context['view'].version

        # trait_property = sami_dr1_sample[data['astro_object']][data['trait'][data['trait_property']]]

        # if isinstance(trait, traits.Map2D):
        #     context['trait_2D_map'] = True

        context['trait_2D_map'] = renderer_context['view'].trait_2D_map

        return context

    @property
    def template(self):
        if hasattr(self.renderer_context['view'], "template"):
            return self.renderer_context['view'].template
        else:
            return 'rest_framework/api.html'


class TraitPropertyRenderer(restapi_app.renderers.ExtendBrowsableAPIRenderer):
    def __repr__(self):
        return 'TraitPropertyRenderer'

    def get_context(self, data, accepted_media_type, renderer_context):
        """ Add reserved keys to the context so the template knows not to iterate over these keys, rather,
        they will be explicitly positioned. """

        context = super().get_context(data, accepted_media_type, renderer_context)
        context['sample'] = renderer_context['view'].sample
        context['astro_object'] = renderer_context['view'].astro_object
        context['trait'] = renderer_context['view'].trait
        context['subtrait'] = renderer_context['view'].subtrait
        context['template'] = renderer_context['view'].template
        context['trait_2D_map'] = renderer_context['view'].trait_2D_map
        context['url_above'] = renderer_context['view'].url_above
        context['side_bar_explicit_render'] = ['description']

        return context

    @property
    def template(self):
        if hasattr(self.renderer_context['view'], "template"):
            return self.renderer_context['view'].template
        else:
            return 'rest_framework/api.html'
