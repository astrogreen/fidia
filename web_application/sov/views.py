import collections
from django.conf import settings

from asvo.fidia_samples_archives import sami_dr1_sample, sami_dr1_archive as ar

from rest_framework import renderers, viewsets, status, mixins
from rest_framework.response import Response

import restapi_app.renderers
import restapi_app.serializers
import restapi_app.exceptions
import restapi_app.renderers

import sov.serializers

from fidia.archive import sami


class SOVListSurveysViewSet(viewsets.ViewSet):
    class SOVListRenderer(restapi_app.renderers.ExtendBrowsableAPIRenderer):
        template = 'sov/list.html'

    renderer_classes = (SOVListRenderer, renderers.JSONRenderer)

    def list(self, request, pk=None, sample_pk=None, format=None):
        """
        List all available objects in fidia
         - this will have autocomplete form
        """
        try:
            sami_dr1_sample
        except KeyError:
            return Response(status=status.HTTP_404_NOT_FOUND)
        except ValueError:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        serializer_class = sov.serializers.SOVListSurveysSerializer
        serializer = serializer_class(
            instance=sami_dr1_sample, many=True,
            context={'request': request},
        )
        return Response(serializer.data)


class SOVRetrieveObjectViewSet(mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    """
    SOV retrieve single object.
    Responds with only the schema, the available traits for this AO, and
     the url of each trait. Will make AJAX calls for trait data.

    """

    class SOVDetailRenderer(restapi_app.renderers.ExtendBrowsableAPIRenderer):
        template = 'sov/detail.html'

    renderer_classes = (SOVDetailRenderer, renderers.JSONRenderer)

    def retrieve(self, request, pk=None, sample_pk=None, format=None):

        try:
            astroobject = sami_dr1_sample[pk]
        except KeyError:
            return Response(status=status.HTTP_404_NOT_FOUND)
        except ValueError:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        serializer_class = sov.serializers.SOVRetrieveSerializer

        sorted_schema = dict(collections.OrderedDict(ar.schema(by_trait_name=True)))

        serializer = serializer_class(
            instance=astroobject, many=False,
            context={
                'request': request,
                'schema': sorted_schema,
                # 'key_info': key_info
            }
        )

        return Response(serializer.data)