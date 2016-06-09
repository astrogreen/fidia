import random, collections, logging, json, requests, zipfile, io
import django.core.exceptions
from django.contrib.auth.models import User
from django.conf import settings
from django.http import HttpResponse

from rest_framework import generics, permissions, renderers, mixins, views, viewsets, status, mixins, exceptions
from rest_framework.response import Response
from rest_framework.settings import api_settings

import restapi_app.permissions
import restapi_app.exceptions
import restapi_app.renderers

import data_browser.serializers
import data_browser.renderers

# from fidia.archive.asvo_spark import AsvoSparkArchive

# log = logging.getLogger(__name__)

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

    renderer_classes = (GAMARenderer,) + tuple(api_settings.DEFAULT_RENDERER_CLASSES)

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

    renderer_classes = (SampleRenderer,) + tuple(api_settings.DEFAULT_RENDERER_CLASSES)

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

    renderer_classes = (AstroObjectRenderer,) + tuple(api_settings.DEFAULT_RENDERER_CLASSES)

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