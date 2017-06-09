from collections import OrderedDict
import requests
import time

from operator import itemgetter, attrgetter
from rest_framework.reverse import reverse
# from rest_framework.decorators import detail_route, list_route
from rest_framework import generics, permissions, renderers, mixins, views, viewsets, status, mixins, exceptions, renderers
from rest_framework.response import Response

import xml.etree.ElementTree as ET

from astropy import units as unit
from astropy.coordinates import SkyCoord

import search.serializers
# from search.helpers.dummy_positions import DUMMY_POSITIONS
from sov.helpers.dummy_data.astro_object import ARCHIVE


def get_archive():
    return ARCHIVE


class AstronomicalObjects(viewsets.ReadOnlyModelViewSet):
    """
    Read-only access to the DC archive list of available astronomical objects.
    This endpoint supports the react-app Object Search component.

    **Actions**
     list:
      Return a list of available astronomic objects in the DC archive.
      
     retrieve:
      Return the given astronomical object meta data only (use sov to get data)     
    """
    serializer_class = search.serializers.AstroObjectList
    queryset = get_archive().values()

    def list(self, request, *args, **kwargs):
        queryset = list(get_archive().values())
        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def retrieve(self, request, pk=None, *args, **kwargs):
        # Note, ARCHIVE[pk] will except if obj does not exist, .get(pk) returns None
        instance = get_archive().get(pk)
        serializer = search.serializers.AstroObjectRetrieve(instance=instance, many=False)
        return Response(serializer.data)


FILTERBY_DOC_STRING = (r"""
    Filter objects in the DC archive by:

    keyword [adcid, name, survey]:
    Return objects with keyword value containing the search term.

    position:
    Return only objects in the DC archive around an on-sky position.
    Accepts ra,dec (hms/deg) position (radius optional, default 3").
      **Valid formats:
       01:12:02.23,+49:28:35.0
       018.0093158, +49.4763969
""")


class FilterBy(views.APIView):
    # Root view for filter-by, returns available urls for various types of filter
    # (keyword or position)
    def get(self, request, *args, **kwargs):
        return Response({
            'urls': [reverse('search:filter-by', kwargs={"filter_term": "adcid"}, request=request),
                     reverse('search:filter-by', kwargs={"filter_term": "name"}, request=request),
                     reverse('search:filter-by', kwargs={"filter_term": "survey"}, request=request),
                     reverse('search:filter-by', kwargs={"filter_term": "position"}, request=request)]
        })
FilterBy.__doc__ = FILTERBY_DOC_STRING


class FilterByTerm(generics.CreateAPIView):
    # Filter by a keyword or position
    queryset = get_archive().values()
    available_keywords = ['adcid', 'name', 'survey']

    serializer_action_classes = {
        'adcid': search.serializers.FilterByADCID,
        'name': search.serializers.FilterByName,
        'survey': search.serializers.FilterBySurvey,
        'position': search.serializers.FilterByPosition,
    }

    filter_serializer_classes = {
        'adcid': search.serializers.AOListByADCID,
        'name': search.serializers.AOListByName,
        'survey': search.serializers.AOListBySurvey,
        'position': search.serializers.AOListByPosition,
    }

    def get_serializer_class(self):
        # Override the base method, using a different serializer
        # depending on the url parameter (these serializers govern the fields
        # that are accessible to the route, form rendering, validation)
        filter_term = self.kwargs['filter_term']
        try:
            return self.serializer_action_classes[filter_term]
        except (KeyError, AttributeError):
            return super(FilterByTerm, self).get_serializer_class()

    def get_filter_serializer_class(self):
        # returns the list serializer used to display the results
        filter_term = self.kwargs['filter_term']
        return self.filter_serializer_classes[filter_term]

    def filter_by_position(self, ra=None, dec=None, radius=None):
        """
        
        Args:
            ra: 
            dec: 
            radius: 

        Returns:

        """
        # sniff out unit type
        ra_unit = unit.deg
        dec_unit = unit.deg
        if ':' in ra:
            ra_unit = unit.hourangle
        if ':' in dec:
            dec_unit = unit.hourangle

        c1 = SkyCoord(ra=ra, dec=dec, unit=(ra_unit, dec_unit))

        ra_deg = c1.ra.degree
        dec_deg = c1.dec.degree
        rad_deg = radius / (60 * 60)

        ra_min = ra_deg - 2 * rad_deg
        ra_max = ra_deg + 2 * rad_deg
        dec_min = dec_deg - 2 * rad_deg
        dec_max = dec_deg + 2 * rad_deg
        # t0 = time.time()
        # print(_ra_min, _ra_max, _dec_min, _dec_max)
        data = []
        for key, x in get_archive().items():
            # initial cut around box twice size of radius
            if (x.position['ra'] < ra_max) and (x.position['ra'] > ra_min) and \
                    (x.position['dec'] < dec_max) and (x.position['dec'] > dec_min):
                c2 = SkyCoord(ra=x.position['ra'], dec=x.position['dec'], unit=(unit.deg, unit.deg))
                sep = c1.separation(c2)
                if sep.degree < rad_deg:
                    # print(sep.arcsec)
                    setattr(x, 'separation', sep.arcsec)
                    data.append(x)
        # t1 = time.time()
        # print(t1-t0)
        # todo sort by separation
        return data

    def filter_by_keyword(self, data=None, filter_term=None, search_value=None):
        filtered_list = []
        for key, value in data:
            if str(search_value).lower() in str(getattr(value, filter_term)).lower():
                filtered_list.append(value)
        return filtered_list

    def create(self, request, filter_term=None, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        if filter_term in self.available_keywords:
            _search_value = serializer.data.get(filter_term)
            data = self.filter_by_keyword(data=get_archive().items(), filter_term=filter_term, search_value=_search_value)

        elif filter_term == 'position':
            # note: in python, '==' is for value equality. 'is' is for reference equality!
            _ra = serializer.data.get('ra')
            _dec = serializer.data.get('dec')
            _radius = serializer.data.get('radius')
            data = self.filter_by_position(ra=_ra, dec=_dec, radius=_radius)

        else:
            # print("%s: '%s'" % (elt.tag, str(elt.text).strip()))
            _message = "filter by must be one of the following values: %s" % self.available_keywords
            return Response({'error': _message})

        completed_data = dict(enumerate(data))
        page = self.paginate_queryset(list(completed_data.values()))

        if page is not None:
            filter_serializer_class = self.get_filter_serializer_class()
            filter_serializer = filter_serializer_class(page, many=True)
            # _serializer = search.serializers.AstroObjectList(page, many=True)
            return self.get_paginated_response(filter_serializer.data)

        headers = self.get_success_headers(serializer.data)
        # return each as json using
        filter_serializer_class = self.get_filter_serializer_class()
        filter_serializer = filter_serializer_class(instance=completed_data.values(), many=True)
        return Response(filter_serializer.data, status=status.HTTP_201_CREATED, headers=headers)
FilterByTerm.__doc__ = FILTERBY_DOC_STRING


class NameResolver(generics.CreateAPIView):
    """
    Return top match from NSV (Ned, then Simbad, then VizieR), returning the first likely result.
    """
    serializer_class = search.serializers.NameResolver
    queryset = get_archive().values()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        _url = "http://cdsweb.u-strasbg.fr/cgi-bin/nph-sesame/-oxp/NSV?%s" % serializer.data.get('name')
        r = requests.get(_url)
        root = ET.fromstring(r.text)

        data = OrderedDict()
        for elt in root.iter():
            # print("%s: '%s'" % (elt.tag, str(elt.text).strip()))
            data[elt.tag] = str(elt.text).strip()

        headers = self.get_success_headers(serializer.data)
        return Response(data, status=status.HTTP_201_CREATED, headers=headers)

