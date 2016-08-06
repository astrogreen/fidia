import random, collections, logging, json, requests, zipfile, io
import django.core.exceptions
from django.contrib.auth.models import User
from django.conf import settings
from django.http import HttpResponse

from asvo.fidia_samples_archives import sami_dr1_sample, sami_dr1_archive as ar

from rest_framework import generics, permissions, renderers, mixins, views, viewsets, status, mixins, exceptions
from rest_framework.response import Response
from rest_framework.settings import api_settings
from rest_framework.reverse import reverse

import restapi_app.permissions
import restapi_app.exceptions
import restapi_app.renderers
import restapi_app.utils.helpers

import data_browser.serializers
import data_browser.renderers

import fidia.exceptions
from fidia.traits import Trait, TraitProperty, TraitRegistry, TraitKey

log = logging.getLogger(__name__)


class DataBrowserViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):

    class DataBrowserRenderer(restapi_app.renderers.ExtendBrowsableAPIRenderer):
        template = 'data_browser/data_browser_root/root.html'
    renderer_classes = (DataBrowserRenderer,) + tuple(api_settings.DEFAULT_RENDERER_CLASSES)

    def list(self, request, pk=None, format=None):
        # Request available samples from FIDIA
        samples = ["sami", "gama"]

        serializer_class = data_browser.serializers.DataBrowserSerializer
        serializer = serializer_class(
            many=False, instance=sami_dr1_sample,
            context={'request': request, 'samples': samples},
        )
        return Response(serializer.data)


class SampleViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    """
    Viewset for Sample route. Provides List view only.
    """
    class SampleRenderer(restapi_app.renderers.ExtendBrowsableAPIRenderer):
        template = 'data_browser/sample/sample-list.html'

    renderer_classes = (SampleRenderer,) + tuple(api_settings.DEFAULT_RENDERER_CLASSES)
    breadcrumb_list = []

    def list(self, request, pk=None, sample_pk=None, format=None):

        SampleViewSet.breadcrumb_list.extend([str(sample_pk).upper()])

        if sample_pk == 'gama':
            return Response({"sample": "gama", "in_progress": True})

        else:
            try:
                # TODO ask FIDIA what it's got for for sample_pk
                sami_dr1_sample
            except KeyError:
                return Response(status=status.HTTP_404_NOT_FOUND)
            except ValueError:
                return Response(status=status.HTTP_400_BAD_REQUEST)

            serializer_class = data_browser.serializers.SampleSerializer
            serializer = serializer_class(
                instance=sami_dr1_sample, many=False,
                context={'request': request, 'sample': sample_pk},
                depth_limit=0,
            )
            return Response(serializer.data)


class AstroObjectViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):

    class AstroObjectRenderer(restapi_app.renderers.ExtendBrowsableAPIRenderer):
        template = 'data_browser/astroobject/astroobject-list.html'

        # def get_context(self, data, accepted_media_type, renderer_context):
        #     context = super().get_context(data, accepted_media_type, renderer_context)
        #     context['trait_short_descriptions'] = renderer_context['view'].trait_short_descriptions
        #     context['trait_pretty_names'] = renderer_context['view'].trait_pretty_names
        #     return context


    renderer_classes = (AstroObjectRenderer,) + tuple(api_settings.DEFAULT_RENDERER_CLASSES)
    breadcrumb_list = []

    def list(self, request, pk=None, sample_pk=None, astroobject_pk=None, format=None):

        AstroObjectViewSet.breadcrumb_list.extend([str(sample_pk).upper(), astroobject_pk])
        try:
            astro_object = sami_dr1_sample[astroobject_pk]
            assert isinstance(astro_object, fidia.AstronomicalObject)
        except fidia.exceptions.NotInSample:
            message = 'Object ' + astroobject_pk + ' Not Found'
            raise restapi_app.exceptions.CustomValidation(detail=message, field='detail', status_code=status.HTTP_404_NOT_FOUND)
        except KeyError:
            return Response(data={}, status=status.HTTP_404_NOT_FOUND)
        except ValueError:
            return Response(data={}, status=status.HTTP_400_BAD_REQUEST)

        serializer_class = data_browser.serializers.AstroObjectSerializer
        url_kwargs = {
            'astroobject_pk': astroobject_pk,
            'sample_pk': sample_pk,
        }
        astro_object_url = reverse("data_browser:astroobject-list", kwargs=url_kwargs, request=request)
        # Dict of available traits
        trait_registry = ar.available_traits
        trait_info = {}
        for trait_type in trait_registry.get_trait_types():

            # Get info for a trait_key (trait name) filtered by trait type
            trait_info[trait_type] = {}

            # Descriptions
            trait_info[trait_type]["description"] = ""
            trait_info[trait_type]["traits"] = {}

            for trait_name in trait_registry.get_trait_names(trait_type_filter=trait_type):

                default_trait_key = trait_registry.update_key_with_defaults(trait_name)
                trait_class = trait_registry.retrieve_with_key(default_trait_key)

                # url
                url_kwargs = {
                    'trait_pk': trait_name,
                    'astroobject_pk': astroobject_pk,
                    'sample_pk': sample_pk,
                }
                trait_name_url = reverse("data_browser:trait-list", kwargs=url_kwargs, request=request)

                # Pretty Name
                # - trait_type
                trait_info[trait_type]["pretty_name"] = trait_class.get_pretty_name()

                # - trait_name
                trait_name_pretty_name = trait_class.get_pretty_name(TraitKey.split_trait_name(trait_name)[1])

                # Descriptions
                # - trait_type description
                trait_type_short_description = trait_class.get_description()
                trait_info[trait_type]["description"] = trait_type_short_description

                # - trait_name description
                trait_name_short_description = None

                # Formats
                trait_name_formats = []
                for r in TraitViewSet.renderer_classes:
                    f = str(r.format)
                    if f != "api": trait_name_formats.append(f)

                # Branches
                trait_name_branches = {str(tk.branch).replace("None", "default"): astro_object_url + str(tk.replace(version=None))
                                        for tk in trait_registry.get_all_traitkeys(trait_name_filter=trait_name)}

                trait_info[trait_type]["traits"][trait_name] = {"url": trait_name_url,
                                                                "pretty_name": trait_name_pretty_name,
                                                                "description": trait_name_short_description,
                                                                "branches": trait_name_branches,
                                                                "formats": trait_name_formats}

        serializer = serializer_class(
            instance=astro_object, many=False,
            context={
                'sample': sample_pk,
                'astroobject': astroobject_pk,
                'request': request,
                'available_traits': trait_info
            }
        )
        return Response(serializer.data)


class TraitViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    """
    Trait Viewset
    """

    def __init__(self, sub_trait_list=None, *args, **kwargs):
        self.sub_trait_list = sub_trait_list

    breadcrumb_list = []

    class TraitRenderer(restapi_app.renderers.ExtendBrowsableAPIRenderer):

        def __init__(self, sub_trait_list_extended=None, *args, **kwargs):
            self.template = 'data_browser/trait/trait-list.html'

        def get_context(self, data, accepted_media_type, renderer_context):
            """ Add reserved keys to the context so the template knows not to iterate over these keys, rather,
            they will be explicitly positioned. """

            context = super().get_context(data, accepted_media_type, renderer_context)

            context['fidia_keys'] = ['sample', 'astroobject', 'trait', 'trait_key']

            context['side_bar_explicit_render'] = ['description', 'documentation']

            # These will be explicitly rendered for a trait, all else will be iterated over in the side bar
            context['trait_properties'] = ['value']

            context['trait_property_keywords'] = ["short_name", "pretty_name", "description", "documentation", "url",
                                                  "name", "type", "value", ]

            trait = sami_dr1_sample[data['astroobject']][data['trait']]

            context['sub_traits'] = [sub_trait.trait_name for sub_trait in trait.get_all_subtraits()]

            context['reserved_keywords'] = ['pretty_name', 'short_name', 'branch', 'version',
                                            'all_branches_versions', ] + \
                                           context['side_bar_explicit_render'] + \
                                           context['fidia_keys'] + \
                                           context['trait_properties'] + \
                                           context['sub_traits']
            # context['html_documentation'] = renderer_context['view'].documentation_html
            # context['pretty_name'] = renderer_context['view'].pretty_name
            # context['short_description'] = renderer_context['view'].short_description
            return context

    renderer_classes = (TraitRenderer, renderers.JSONRenderer, data_browser.renderers.FITSRenderer)

    def list(self, request, pk=None, sample_pk=None, astroobject_pk=None, trait_pk=None, format=None):

        TraitViewSet.breadcrumb_list.extend([str(sample_pk).upper(), astroobject_pk, trait_pk])

        # Dict of available traits
        trait_registry = ar.available_traits
        default_trait_key = trait_registry.update_key_with_defaults(trait_pk)

        try:
            trait = sami_dr1_sample[astroobject_pk][trait_pk]
        except fidia.exceptions.NotInSample:
            message = 'Object ' + astroobject_pk + ' Not Found'
            raise restapi_app.exceptions.CustomValidation(detail=message, field='detail', status_code=status.HTTP_404_NOT_FOUND)
        except fidia.exceptions.UnknownTrait:
            message = 'Not found: Object ' + astroobject_pk + ' does not have property ' + trait_pk
            raise restapi_app.exceptions.CustomValidation(detail=message, field='detail', status_code=status.HTTP_404_NOT_FOUND)
        except KeyError:
            return Response(status=status.HTTP_404_NOT_FOUND)
        except ValueError:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        serializer_class = data_browser.serializers.TraitSerializer

        serializer = serializer_class(
            instance=trait, many=False,
            context={
                'request': request,
                'sample': sample_pk,
                'astroobject': astroobject_pk,
                'trait': trait_pk,
                'trait_key': default_trait_key,
            }
        )

        # Add some data to the view so that it can be made available to the renderer.
        #
        # This data is not included in the actual data of the serialized object
        # (though that is possible, see the implementations of the Serializers)
        # self.documentation_html = trait.get_documentation('html')
        # self.pretty_name = trait.get_pretty_name()
        # self.short_description = trait.get_description()

        return Response(serializer.data)

    def finalize_response(self, request, response, *args, **kwargs):
        response = super().finalize_response(request, response, *args, **kwargs)
        if response.accepted_renderer.format == 'fits':
            filename = "{obj_id}-{trait}.fits".format(
                obj_id=kwargs['astroobject_pk'],
                trait=kwargs['trait_pk'])
            response['content-disposition'] = "attachment; filename=%s" % filename
        return response


class DynamicViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):

    def list(self, request, sample_pk=None, astroobject_pk=None, trait_pk=None, dynamic_pk=None, format=None):

        # Determine what we're looking at.
        # type_for_trait_path requires the trait_key and current "path"
        path = list(dynamic_pk.split('/'))

        path.insert(0, trait_pk)

        if issubclass(ar.type_for_trait_path(path), Trait):
            trait_pointer = sami_dr1_sample[astroobject_pk]
            for elem in path:
                trait_pointer = trait_pointer[elem]
            serializer = data_browser.serializers.TraitSerializer(
                instance=trait_pointer, many=False,
                context={'request': request}
            )

        elif issubclass(ar.type_for_trait_path(path), TraitProperty):
            trait_pointer = sami_dr1_sample[astroobject_pk]
            for elem in path[:-1]:
                trait_pointer = trait_pointer[elem]
            trait_property = getattr(trait_pointer, path[-1])
            serializer = data_browser.serializers.TraitPropertySerializer(
                instance=trait_property, many=False,
                context={'request': request}
            )
        else:
            raise Exception("programming error")

        return Response(serializer.data)


class TraitPropertyViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):

    class TraitPropertyRenderer(restapi_app.renderers.ExtendBrowsableAPIRenderer):
        template = 'data_browser/trait_property/traitproperty-list.html'

    renderer_classes = (TraitPropertyRenderer, renderers.JSONRenderer)

    def list(self, request, pk=None, sample_pk=None, astroobject_pk=None, trait_pk=None, traitproperty_pk=None, format=None):
        try:
            # address trait properties via . not []
            trait_property = getattr(sami_dr1_sample[astroobject_pk][trait_pk], traitproperty_pk)
        except KeyError:
            return Response(status=status.HTTP_404_NOT_FOUND)
        except ValueError:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        except AttributeError:
            raise restapi_app.exceptions.NoPropertyFound("No property %s" % traitproperty_pk)
            # return Response(status=status.HTTP_404_NOT_FOUND)

        serializer_class = data_browser.serializers.AstroObjectTraitPropertySerializer
        serializer = serializer_class(
            instance=trait_property, many=False,
            context={'request': request}
        )

        # Add some data to the view so that it can be made available to the renderer.
        #
        # This data is not included in the actual data of the serialized object
        # (though that is possible, see the implementations of the Serializers)
        self.documentation_html = trait_property.get_documentation('html')
        self.pretty_name = trait_property.get_pretty_name()
        self.short_description = trait_property.get_description()

        return Response(serializer.data)

    def finalize_response(self, request, response, *args, **kwargs):
        response = super().finalize_response(request, response, *args, **kwargs)
        if response.accepted_renderer.format == 'fits':
            filename = "{astroobject_pk}-{trait_pk}-{traitproperty_pk}.fits".format(**kwargs)
            response['content-disposition'] = "attachment; filename=%s" % filename
        return response


