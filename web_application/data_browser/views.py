import random, collections, logging, json, requests, zipfile, io
import django.core.exceptions
from django.contrib.auth.models import User
from django.conf import settings
from django.http import HttpResponse

from asvo.fidia_samples_archives import sami_dr1_sample

from rest_framework import generics, permissions, renderers, mixins, views, viewsets, status, mixins, exceptions
from rest_framework.response import Response
from rest_framework.settings import api_settings

import restapi_app.permissions
import restapi_app.exceptions
import restapi_app.renderers
import restapi_app.utils.helpers

import data_browser.serializers
import data_browser.renderers

import fidia.exceptions
from fidia.traits import Trait, TraitProperty, TraitRegistry

log = logging.getLogger(__name__)

class GAMAViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):

    class GAMARenderer(restapi_app.renderers.ExtendBrowsableAPIRenderer):
        template = 'data_browser/sample/inprogress.html'

    renderer_classes = (GAMARenderer,) + tuple(api_settings.DEFAULT_RENDERER_CLASSES)

    def list(self, request, pk=None, sample_pk=None, format=None):
        try:
            sami_dr1_sample
        except KeyError:
            return Response(status=status.HTTP_404_NOT_FOUND)
        except ValueError:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        return Response({'nodata': True})


class SAMIViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):

    class SampleRenderer(restapi_app.renderers.ExtendBrowsableAPIRenderer):
        template = 'data_browser/sample/sample-list.html'

    renderer_classes = (SampleRenderer,) + tuple(api_settings.DEFAULT_RENDERER_CLASSES)

    def list(self, request, pk=None, sample_pk=None, format=None):
        try:
            sami_dr1_sample
        except KeyError:
            return Response(status=status.HTTP_404_NOT_FOUND)
        except ValueError:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        serializer_class = data_browser.serializers.SampleSerializer
        serializer = serializer_class(
            instance=sami_dr1_sample, many=False,
            context={'request': request},
            depth_limit=1
        )
        return Response(serializer.data)


class AstroObjectViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):

    # TODO ensure proper http status code is returned (page not found) on non-identifiable traits

    class AstroObjectRenderer(restapi_app.renderers.ExtendBrowsableAPIRenderer):
        template = 'data_browser/astroobject/astroobject-list.html'

    renderer_classes = (AstroObjectRenderer,) + tuple(api_settings.DEFAULT_RENDERER_CLASSES)

    def list(self, request, pk=None, sample_pk=None, galaxy_pk=None, format=None):

        try:
            astroobject = sami_dr1_sample[galaxy_pk]
        except fidia.exceptions.NotInSample:
            message = 'Object ' + galaxy_pk + ' Not Found'
            raise restapi_app.exceptions.CustomValidation(detail=message, field='detail', status_code=status.HTTP_404_NOT_FOUND)
        except KeyError:
            return Response(data={}, status=status.HTTP_404_NOT_FOUND)
        except ValueError:
            return Response(data={}, status=status.HTTP_400_BAD_REQUEST)

        serializer_class = data_browser.serializers.AstroObjectSerializer

        # Get schema for this archive's astro object and sort alphabetically
        sorted_schema_temp = {}

        for key, value in sorted(ar.schema(by_trait_name=True).items()):
            sorted_schema_temp[key] = collections.OrderedDict(sorted(value.items()))

        sorted_schema = collections.OrderedDict(sorted(sorted_schema_temp.items()))

        # Get available traits (minus qualifier) for this archive's astro object
        # to provide groupings (line maps, velocity maps etc) in ao view.
        available_trait_set = ar.available_traits.get_traits()
        trait_list = []

        for ty in available_trait_set:
            trait_list.append(ty.trait_type)

        trait_list = restapi_app.utils.helpers.unique_list(trait_list)

        serializer = serializer_class(
            instance=astroobject, many=False,
            context={
                'request': request,
                'schema': sorted_schema,
                'trait_list': sorted(trait_list)
            }
        )

        return Response(serializer.data)


class TraitViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):

    class TraitRenderer(restapi_app.renderers.ExtendBrowsableAPIRenderer):
        template = 'data_browser/trait/trait-list.html'

        def get_context(self, data, accepted_media_type, renderer_context):
            context = super().get_context(data, accepted_media_type, renderer_context)
            context['html_documentation'] = renderer_context['view'].documentation_html
            context['pretty_name'] = renderer_context['view'].pretty_name
            context['short_description'] = renderer_context['view'].short_description
            return context

    renderer_classes = (TraitRenderer, renderers.JSONRenderer, data_browser.renderers.FITSRenderer)

    def list(self, request, pk=None, sample_pk=None, galaxy_pk=None, trait_pk=None, format=None):
        print('TRAIT:'+trait_pk)
        try:
            trait = sami_dr1_sample[galaxy_pk][trait_pk]
        except fidia.exceptions.NotInSample:
            message = 'Object ' + galaxy_pk + ' Not Found'
            raise restapi_app.exceptions.CustomValidation(detail=message, field='detail', status_code=status.HTTP_404_NOT_FOUND)
        except fidia.exceptions.UnknownTrait:
            message = 'Not found: Object ' + galaxy_pk + ' does not have property ' + trait_pk
            raise restapi_app.exceptions.CustomValidation(detail=message, field='detail', status_code=status.HTTP_404_NOT_FOUND)
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

        # Add some data to the view so that it can be made available to the renderer.
        #
        # This data is not included in the actual data of the serialized object
        # (though that is possible, see the implementations of the Serializers)
        self.documentation_html = trait.get_documentation('html')
        self.pretty_name = trait.get_pretty_name()
        self.short_description = trait.get_description()

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
            trait_property = getattr(sami_dr1_sample[galaxy_pk][trait_pk], traitproperty_pk)
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
            filename = "{galaxy_pk}-{trait_pk}-{traitproperty_pk}.fits".format(**kwargs)
            response['content-disposition'] = "attachment; filename=%s" % filename
        return response


class SubTraitPropertyViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):

    def list(self, request, pk=None, galaxy_pk=None, trait_pk=None, dynamic_pk=None, format=None):
        print(dynamic_pk)
        print(trait_pk)
        print(galaxy_pk)
        # @property
        # def dynamic_property_first_of_type(self, dynamic_pk):
            # split on /

        # Determine what we're looking at.
        path = list(dynamic_pk.split('/'))

        path.insert(0, trait_pk)
        # return Response({"data": str(ar.type_for_trait_path(path))})
        print(ar.type_for_trait_path(path))
        if issubclass(ar.type_for_trait_path(path), Trait):
            trait_pointer = sami_dr1_sample[galaxy_pk]
            for elem in path:
                trait_pointer = trait_pointer[elem]
            serializer = data_browser.serializers.AstroObjectTraitSerializer(
                instance=trait_pointer, many=False,
                context={'request': request}
            )

        elif issubclass(ar.type_for_trait_path(path), TraitProperty):
            trait_pointer = sami_dr1_sample[galaxy_pk]
            for elem in path[:-1]:
                trait_pointer = trait_pointer[elem]
            trait_property = getattr(trait_pointer, path[-1])
            serializer = data_browser.serializers.AstroObjectTraitPropertySerializer(
                instance=trait_property, many=False,
                context={'request': request}
            )
        else:
            raise Exception("programming error")

        return Response(serializer.data)


        # Return a list of components
        dynamic_components = dynamic_pk.split('/')
        # first component distinction: ST/TP
        return Response({'dynamic_pk': dynamic_components})


class Checkout(views.APIView):
    renderer_classes = [renderers.StaticHTMLRenderer]

    def get(self, request, format=None):
        """
        Return Zip of urls
        """

        url = 'http://127.0.0.1:8000/asvo/data/sami/9352/velocity_map/?format=fits'

        # get data from url
        request_data = requests.get(url)

        print(request_data)
        print(request_data.status_code)
        print(request_data.headers)
        print(request_data.headers['content-disposition'])

        # # set zip filename OK
        zip_filename = "download.zip"

        # Create zip in-memory rather than writing out to file
        # This is where the zip will be written
        buff = io.BytesIO()
        # This is the zip file
        zip_archive = zipfile.ZipFile(buff, 'w')

        temp = []
        for i in range(4):
            # One 'memory file' for each file I want in my zip archive
            temp.append(io.BytesIO())

        # Writing something to the files, to be able to
        # distinguish them
        # HERE TODO write in url data
        # data is already in bytes format!
        temp[0].write(request_data.content)
        temp[1].write(bytes('second in-mem temp file', 'UTF-8'))
        temp[2].write(bytes('third in-mem temp file', 'UTF-8'))
        temp[3].write(bytes('fourth in-mem temp file', 'UTF-8'))

        for i in range(4):
            # The zipfile module provide the 'writestr' method.
            # First argument is the name you want for the file
            # inside your zip, the second argument is the content
            # of the file, in string format. StringIO provides
            # you with the 'getvalue' method to give you the full
            # content as a string
            if i == 0:
                zip_archive.writestr('temp'+str(i)+'.fits',
                                 temp[i].getvalue())
            else:
                zip_archive.writestr('temp'+str(i)+'.txt',
                                 temp[i].getvalue())

        # Close the zip (sitting in the buff ByteIO object)
        zip_archive.close()

        # Visualize zip structure
        print(zip_archive.printdir())

        # Send file back OK
        resp = HttpResponse(buff.getvalue(), content_type="application/x-zip-compressed")
        resp['Content-Disposition'] = 'attachment; filename=%s' % zip_filename

        return resp


class DataCheckoutView(viewsets.ViewSet):
    """
    You can do:
    http --form POST http://127.0.0.1:8000/asvo/data/checkout/ urls="http://127.0.0.1:8000/asvo/data/sami/9352/velocity_map/?format=fits, http://127.0.0.1:8000/asvo/data/sami/9352/line_map-SII6716/?format=fits" > zippyfile.zip
    """
    # Required for the Browsable API renderer to have a nice form.
    serializer_class = data_browser.serializers.DataCheckoutSerializer

    def list(self, request):
        return Response({'data': 'in the view - list'})

    def create(self, request):
        resp_text = 'response text'
        #
        try:
            url_str = request.data['urls']
        except AttributeError:
            raise restapi_app.exceptions.NoURLSFound

        # Set zip filename (may want this dynamic in future)
        zip_filename = "download.zip"

        # Create zip archive in-memory
        # User BytesIO as fits binary
        buff = io.BytesIO()
        zip_archive = zipfile.ZipFile(buff, 'w')

        # Create temporary arr
        temp = []
        url_list = url_str.split(',')

        for url in url_list:
            request_data = requests.get(url.strip())
            # Get the file name from the request header
            temp_name = request_data.headers['content-disposition'].split('filename=')[1]
            if request_data.status_code == 200:
                # One 'memory file' for each file I want in my zip archive
                temp.append(io.BytesIO())

                # Write to last element in temp arr
                # Will need additional validation here on content type
                temp[-1].write(request_data.content)
                # The zipfile module provide the 'writestr' method.
                # First argument is the name you want for the file
                # inside your zip, the second argument is the content
                # of the file, in byte format.
                zip_archive.writestr(temp_name, temp[-1].getvalue())

        # Close the zip (sitting in the buff ByteIO object)
        zip_archive.close()

        # Visualize zip structure
        print(zip_archive.printdir())

        # Send file back
        resp = HttpResponse(buff.getvalue(), content_type="application/x-zip-compressed")
        resp['Content-Disposition'] = 'attachment; filename=%s' % zip_filename

        return resp