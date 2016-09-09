import random, collections, logging, json, requests, zipfile, io
import django.core.exceptions
from django.contrib.auth.models import User
from django.conf import settings
from django.http import HttpResponse

from asvo.fidia_samples_archives import sami_dr1_sample, sami_dr1_archive as ar

from rest_framework import generics, permissions, renderers, mixins, views, viewsets, status, mixins, exceptions, \
    renderers
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
from fidia.traits import Trait, TraitProperty, TraitKey
from fidia import traits

log = logging.getLogger(__name__)

# TWO_D_PLOT_TYPES = ["line_map", "sfr_map", "velocity_map", "emission_classification_map", "extinction_map"]


class RootViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    """ Viewset for DataBrowser API root. List View only. """

    renderer_classes = (data_browser.renderers.RootRenderer, renderers.JSONRenderer)
    permission_classes = [permissions.AllowAny]

    def list(self, request, pk=None, format=None):
        # Request available samples from FIDIA
        surveys = [{"survey": "sami", "count": sami_dr1_sample.ids.__len__(), "current_version": 1.0},
                   {"survey": "gama", "count": 0, "current_version": 0}]

        self.breadcrumb_list = ['Data Browser']

        serializer_class = data_browser.serializers.RootSerializer
        serializer = serializer_class(
            many=False, instance=sami_dr1_sample,
            context={'request': request, 'surveys': surveys},
        )
        return Response(serializer.data)


class SurveyViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    """
    Viewset for Sample route. Provides List view only.
    """

    renderer_classes = (data_browser.renderers.SurveyRenderer, renderers.JSONRenderer)
    permission_classes = [permissions.AllowAny]

    def list(self, request, pk=None, sample_pk=None, format=None, extra_keyword=None):

        self.breadcrumb_list = ['Data Browser', str(sample_pk).upper()]

        if sample_pk == 'gama':
            return Response({"survey": "gama", "in_progress": True})

        else:
            try:
                # TODO ask FIDIA what it's got for for sample_pk
                sami_dr1_sample
            except KeyError:
                return Response(status=status.HTTP_404_NOT_FOUND)
            except ValueError:
                return Response(status=status.HTTP_400_BAD_REQUEST)

            serializer_class = data_browser.serializers.SurveySerializer
            serializer = serializer_class(
                instance=sami_dr1_sample, many=False,
                context={'request': request, 'survey': sample_pk}
            )
            return Response(serializer.data)


class AstroObjectViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    renderer_classes = (data_browser.renderers.AstroObjectRenderer, renderers.JSONRenderer)
    permission_classes = [permissions.AllowAny]

    def list(self, request, pk=None, sample_pk=None, astroobject_pk=None, format=None):

        self.breadcrumb_list = ['Data Browser', str(sample_pk).upper(), astroobject_pk]

        try:
            astro_object = sami_dr1_sample[astroobject_pk]
            assert isinstance(astro_object, fidia.AstronomicalObject)
        except fidia.exceptions.NotInSample:
            message = 'Object ' + astroobject_pk + ' Not Found'
            raise restapi_app.exceptions.CustomValidation(detail=message, field='detail',
                                                          status_code=status.HTTP_404_NOT_FOUND)
        except KeyError:
            return Response(data={}, status=status.HTTP_404_NOT_FOUND)
        except ValueError:
            return Response(data={}, status=status.HTTP_400_BAD_REQUEST)

        serializer_class = data_browser.serializers.AstroObjectSerializer
        url_kwargs = {
            'astroobject_pk': astroobject_pk,
            'sample_pk': sample_pk,
        }
        astro_object_url = reverse("data_browser:astroobject-list", kwargs=url_kwargs)
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
                trait_name_url = reverse("data_browser:trait-list", kwargs=url_kwargs)

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
                trait_name_branches = {
                    str(tk.branch).replace("None", "default"): astro_object_url + str(tk.replace(version=None))
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
                'available_traits': trait_info,
            }
        )
        return Response(serializer.data)


class TraitViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    """
    Trait Viewset
    """

    def __init__(self, sub_trait_list=None, *args, **kwargs):
        self.sub_trait_list = sub_trait_list
        self.breadcrumb_list = []

    renderer_classes = (
        data_browser.renderers.TraitRenderer, renderers.JSONRenderer, data_browser.renderers.FITSRenderer)
    permission_classes = [permissions.AllowAny]

    def list(self, request, pk=None, sample_pk=None, astroobject_pk=None, trait_pk=None, format=None):

        # Dict of available traits
        trait_registry = ar.available_traits
        default_trait_key = trait_registry.update_key_with_defaults(trait_pk)

        try:
            trait = sami_dr1_sample[astroobject_pk][trait_pk]
        except fidia.exceptions.NotInSample:
            message = 'Object ' + astroobject_pk + ' Not Found'
            raise restapi_app.exceptions.CustomValidation(detail=message, field='detail',
                                                          status_code=status.HTTP_404_NOT_FOUND)
        except fidia.exceptions.UnknownTrait:
            message = 'Not found: Object ' + astroobject_pk + ' does not have property ' + trait_pk
            raise restapi_app.exceptions.CustomValidation(detail=message, field='detail',
                                                          status_code=status.HTTP_404_NOT_FOUND)
        except KeyError:
            return Response(status=status.HTTP_404_NOT_FOUND)
        except ValueError:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        self.breadcrumb_list = ['Data Browser', str(sample_pk).upper(), astroobject_pk, trait.get_pretty_name()]

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


class SubTraitPropertyViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    """
    Dynamic View evaluated on instance type is Trait or Trait property
    This is only one level
    """

    def __init__(self, sample=None, astroobject=None, trait=None, template=None, *args, **kwargs):
        self.sample = sample
        self.astroobject = astroobject
        self.trait = trait
        self.renderer_classes = (data_browser.renderers.SubTraitPropertyRenderer, renderers.JSONRenderer)
        self.permission_classes = [permissions.AllowAny]
        self.trait_2D_map = False

    def list(self, request, sample_pk=None, astroobject_pk=None, trait_pk=None, subtraitproperty_pk=None, format=None):

        # Determine what we're looking at.
        # type_for_trait_path requires the trait_key and current "path"
        path = [subtraitproperty_pk]
        path.insert(0, trait_pk)

        if issubclass(ar.type_for_trait_path(path), Trait):
            self.template = 'data_browser/sub_trait/list.html'
            trait_pointer = sami_dr1_sample[astroobject_pk][trait_pk]

            subtrait_pointer = trait_pointer[subtraitproperty_pk]

            self.type = subtrait_pointer.trait_type

            if isinstance(self.trait, traits.Map2D):
                self.trait_2D_map = True

            # Formats
            formats = []
            for r in TraitViewSet.renderer_classes:
                f = str(r.format)
                if f != "api": formats.append(f)
            self.formats = formats
            self.branch = trait_pointer.branch
            self.version = trait_pointer.version

            serializer = data_browser.serializers.TraitSerializer(
                instance=subtrait_pointer, many=False,
                context={'request': request,
                         'sample': sample_pk,
                         'astroobject': astroobject_pk,
                         'trait': trait_pk,
                         'subtraitproperty': subtraitproperty_pk,
                         'trait_key': str(subtrait_pointer.trait_key),
                         })
            # Set Breadcrumbs for this method
            self.breadcrumb_list = ['Data Browser', str(sample_pk).upper(), astroobject_pk,
                                    trait_pointer.get_pretty_name(),
                                    subtrait_pointer.get_pretty_name()]

        elif issubclass(ar.type_for_trait_path(path), TraitProperty):
            self.template = 'data_browser/trait_property/list.html'
            trait_pointer = sami_dr1_sample[astroobject_pk][trait_pk]
            traitproperty_pointer = getattr(trait_pointer, subtraitproperty_pk)

            self.type = trait_pointer.trait_type
            # self.trait_2D_map = False
            # if self.type in TWO_D_PLOT_TYPES: self.trait_2D_map = True

            # Formats
            formats = []
            for r in TraitViewSet.renderer_classes:
                f = str(r.format)
                if f != "api": formats.append(f)
            self.formats = formats
            self.branch = trait_pointer.branch
            self.version = trait_pointer.version

            # trait_pointer = sami_dr1_sample[astroobject_pk]
            # for elem in path[:-1]:
            #     trait_pointer = trait_pointer[elem]
            # trait_property = getattr(trait_pointer, path[-1])

            serializer = data_browser.serializers.TraitPropertySerializer(
                instance=traitproperty_pointer, many=False,
                context={'request': request,
                         'sample': sample_pk,
                         'astroobject': astroobject_pk,
                         'trait': trait_pk,
                         'subtraitproperty': subtraitproperty_pk,
                         })
            # Set Breadcrumbs for this method
            self.breadcrumb_list = ['Data Browser', str(sample_pk).upper(), astroobject_pk,
                                    trait_pointer.get_pretty_name(),
                                    traitproperty_pointer.get_pretty_name()]

        else:
            raise Exception("programming error")

        # Add some data to the view so that it can be made available to the renderer.
        # This data is not included in the actual data of the serialized object
        # (though that is possible, see the implementations of the Serializers)

        self.sample = sample_pk
        self.astroobject = astroobject_pk
        self.trait = trait_pointer.get_pretty_name()
        url_kwargs = {
            'astroobject_pk': astroobject_pk,
            'sample_pk': sample_pk,
            'trait_pk': trait_pk
        }
        self.trait_url = reverse("data_browser:trait-list", kwargs=url_kwargs)

        return Response(serializer.data)


class TraitPropertyViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    """
    Final level of nesting - this will provide a level to all those sub-trait/traitproperty views.
    Might not even need it - may be able to pass through SubTraitProperty Viewset with carefully managed pks
    """

    def __init__(self, sample=None, astroobject=None, trait=None, template=None, *args, **kwargs):
        self.sample = sample
        self.astroobject = astroobject
        self.trait = trait
        self.permission_classes = [permissions.AllowAny]
        self.renderer_classes = (data_browser.renderers.TraitPropertyRenderer, renderers.JSONRenderer)


    def list(self, request, sample_pk=None, astroobject_pk=None, trait_pk=None, subtraitproperty_pk=None,
             traitproperty_pk=None, format=None):

        elem = getattr(sami_dr1_sample[astroobject_pk][trait_pk][subtraitproperty_pk], traitproperty_pk)
        trait_pointer = sami_dr1_sample[astroobject_pk][trait_pk]
        subtrait_pointer = sami_dr1_sample[astroobject_pk][trait_pk][subtraitproperty_pk]

        self.template = 'data_browser/trait_property/list.html'
        self.astroobject = astroobject_pk
        self.sample = sample_pk
        self.trait = trait_pointer.get_pretty_name()
        self.subtrait = subtrait_pointer.get_pretty_name()

        self.url_above = ''

        url_kwargs = {
            'trait_pk': trait_pk,
            'astroobject_pk': astroobject_pk,
            'sample_pk': sample_pk,
        }
        if subtraitproperty_pk is not None:
            url_kwargs['subtraitproperty_pk'] = subtraitproperty_pk
            self.url_above = reverse("data_browser:subtraitproperty-list", kwargs=url_kwargs)
        else:
            self.url_above = reverse("data_browser:trait-list", kwargs=url_kwargs)

        self.type = subtrait_pointer.trait_type
        self.trait_2D_map = False
        if self.type in TWO_D_PLOT_TYPES: self.trait_2D_map = True;

        serializer = data_browser.serializers.TraitPropertySerializer(
            instance=elem, many=False,
            context={'request': request,
                     'sample': sample_pk,
                     'astroobject': astroobject_pk,
                     'trait': trait_pk,
                     'subtraitproperty': subtraitproperty_pk,
                     'traitproperty': traitproperty_pk
                     }
        )

        self.breadcrumb_list = ['Data Browser', str(sample_pk).upper(), astroobject_pk, trait_pointer.get_pretty_name(),
                                subtrait_pointer.get_pretty_name(), elem.get_pretty_name()]

        return Response(serializer.data)
