import random, collections, logging, importlib
from django.contrib.auth.models import User
from django.conf import settings
import django.core.exceptions

from rest_framework import generics, permissions, renderers, mixins, views, viewsets, status, mixins, exceptions
from rest_framework.response import Response
from rest_framework.settings import api_settings

import restapi_app.permissions
import restapi_app.exceptions
import restapi_app.renderers

import data_browser.serializers
import data_browser.renderers

# from fidia.archive.asvo_spark import AsvoSparkArchive

log = logging.getLogger(__name__)

# from fidia.archive.example_archive import ExampleArchive
# ar = ExampleArchive()
# sample = ar.get_full_sample()

from fidia.archive.sami import SAMITeamArchive
# ar = SAMITeamArchive(
#     "/net/aaolxz/iscsi/data/SAMI/data_releases/v0.9/",
#     "/net/aaolxz/iscsi/data/SAMI/catalogues/" +
#     "sami_sel_20140911_v2.0JBupdate_July2015_incl_nonQCmet_galaxies.fits")

ar = SAMITeamArchive(
    settings.SAMI_TEAM_DATABASE,
    settings.SAMI_TEAM_DATABASE_CATALOG)

sample = ar.get_full_sample()

# >>> ar.schema()
# {'line_map': {'value': 'float.ndarray', 'variance': 'float.ndarray'},
# 'redshift': {'value': 'float'},
# 'spectral_map': {'extra_value': 'float',
#    'galaxy_name': 'string',
#    'value': 'float.array',
#    'variance': 'float.array'},
# 'velocity_map': {'value': 'float.ndarray', 'variance': 'float.ndarray'}}
#
# >>> sample['Gal1']['redshift'].value
# 3.14159
#


class GAMAViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):

    class GAMARenderer(restapi_app.renderers.ExtendBrowsableAPIRenderer):
        template = 'data_browser/sample/inprogress.html'

    renderer_classes = (GAMARenderer, renderers.JSONRenderer)

    def list(self, request, pk=None, sample_pk=None, format=None):
        try:
            sample
        except KeyError:
            return Response(status=status.HTTP_404_NOT_FOUND)
        except ValueError:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        return Response({'nodata': True})


class SAMIViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):

    class SampleRenderer(restapi_app.renderers.ExtendBrowsableAPIRenderer):
        template = 'data_browser/sample/sample-list.html'

    renderer_classes = (SampleRenderer, renderers.JSONRenderer)

    def list(self, request, pk=None, sample_pk=None, format=None):
        try:
            sample
        except KeyError:
            return Response(status=status.HTTP_404_NOT_FOUND)
        except ValueError:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        serializer_class = data_browser.serializers.SampleSerializer
        serializer = serializer_class(
            instance=sample, many=False,
            context={'request': request},
            depth_limit=1
        )
        return Response(serializer.data)


class AstroObjectViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):

    # TODO ensure proper http status code is returned (page not found) on non-identifiable traits

    class AstroObjectRenderer(restapi_app.renderers.ExtendBrowsableAPIRenderer):
        template = 'data_browser/astroobject/astroobject-list.html'

    # renderer_classes = (AstroObjectRenderer, renderers.JSONRenderer)
    renderer_classes = (AstroObjectRenderer,) + tuple(api_settings.DEFAULT_RENDERER_CLASSES)

    # try:
    #     default_renderer_classes_list = settings.REST_FRAMEWORK['DEFAULT_RENDERER_CLASSES']
    #     print(api_settings.DEFAULT_RENDERER_CLASSES)
    #     default_renderer_classes_instances = (AstroObjectRenderer,)
    #     for this in default_renderer_classes_list:
    #         package, module, class_name = this.split('.')
    #         somemodule = importlib.import_module(package + "." + module)
    #         default_renderer_classes_instances = default_renderer_classes_instances + (getattr(somemodule, class_name),)
    # except:
    #     raise django.core.exceptions.ImproperlyConfigured('Default renderer classes must be set in settings.py')
    #
    # renderer_classes = default_renderer_classes_instances

    def list(self, request, pk=None, sample_pk=None, galaxy_pk=None, format=None):
        # def get_serializer_context(self):
        #     """
        #     pass request attribute to serializer - add schema attribute
        #     """
        #     return {
        #         'request': self.request,
        #         'schema': ar.schema()
        #     }

        try:
            astroobject = sample[galaxy_pk]
        except KeyError:
            return Response(status=status.HTTP_404_NOT_FOUND)
        except ValueError:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        serializer_class = data_browser.serializers.AstroObjectSerializer

        sorted_schema = dict(collections.OrderedDict(ar.schema()))

        serializer = serializer_class(
            instance=astroobject, many=False,
            context={
                'request': request,
                'schema': sorted_schema
                }
        )

        return Response(serializer.data)


class TraitViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):

    class TraitRenderer(restapi_app.renderers.ExtendBrowsableAPIRenderer):
        template = 'data_browser/trait/trait-list.html'

    renderer_classes = (TraitRenderer, renderers.JSONRenderer, data_browser.renderers.FITSRenderer)

    def list(self, request, pk=None, sample_pk=None, galaxy_pk=None, trait_pk=None, format=None):
        log.debug("Format requested is '%s'", format)

        try:
            trait = sample[galaxy_pk][trait_pk]
        except KeyError:
            return Response(status=status.HTTP_404_NOT_FOUND)
        except ValueError:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        serializer_class = data_browser.serializers.AstroObjectTraitSerializer
        serializer = serializer_class(
            instance=trait, many=False,
            context={
                'request': request,
            }
        )

        return Response(serializer.data)

    def finalize_response(self, request, response, *args, **kwargs):
        response = super().finalize_response(request, response, *args, **kwargs)
        if response.accepted_renderer.format == 'fits':
            filename = "{obj_id}-{trait}.fits".format(
                obj_id=kwargs['galaxy_pk'],
                trait=kwargs['trait_pk'])
            response['content-disposition'] = "attachment; filename=%s" % filename
        return response


class TraitPropertyViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):

    class TraitPropertyRenderer(restapi_app.renderers.ExtendBrowsableAPIRenderer):
        template = 'data_browser/trait_property/traitproperty-list.html'

    renderer_classes = (TraitPropertyRenderer, renderers.JSONRenderer)

    def list(self, request, pk=None, sample_pk=None, galaxy_pk=None, trait_pk=None, traitproperty_pk=None, format=None):
        try:
            # address trait properties via . not []
            trait_property = getattr(sample[galaxy_pk][trait_pk], traitproperty_pk)
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
        return Response(serializer.data)

    def finalize_response(self, request, response, *args, **kwargs):
        response = super().finalize_response(request, response, *args, **kwargs)
        if response.accepted_renderer.format == 'fits':
            filename = "{galaxy_pk}-{trait_pk}-{traitproperty_pk}.fits".format(**kwargs)
            response['content-disposition'] = "attachment; filename=%s" % filename
        return response


class SubTraitPropertyViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):

    def list(self, request, pk=None, galaxy_pk=None, trait_pk=None, dynamic_pk=None, format=None):
        # @property
        # def dynamic_property_first_of_type(self, dynamic_pk):
            # split on /

        # Return a list of components
        dynamic_components = dynamic_pk.split('/')
        # first component distinction: ST/TP
        return Response({'dynamic_pk': dynamic_components})



