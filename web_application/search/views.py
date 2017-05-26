from collections import OrderedDict
import requests
from operator import itemgetter, attrgetter
from rest_framework.reverse import reverse
# from rest_framework.decorators import detail_route, list_route
from rest_framework import generics, permissions, renderers, mixins, views, viewsets, status, mixins, exceptions, renderers
from rest_framework.response import Response

import xml.etree.ElementTree as ET

from astropy import units as unit
from astropy.coordinates import SkyCoord

import search.serializers
from search.helpers.dummy_positions import DUMMY_POSITIONS


class AstroObject(object):
    def __init__(self, **kwargs):
        for field in ('id', 'name', 'owner', 'surveys', 'status', 'position'):
            setattr(self, field, kwargs.get(field, None))

archive = OrderedDict()
lower = 0
upper = 999
for i in range(lower, upper):
    # id is unique
    _adc_id = 'DC' + str(i)
    _name = DUMMY_POSITIONS[i][0]
    archive[_adc_id] = AstroObject(
        id=_adc_id,
        name=_name,
        owner='sami',
        survey="sami",
        status=['new', 'released'],
        position={"ra": DUMMY_POSITIONS[i][2], "dec": DUMMY_POSITIONS[i][1]},
    )


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
    queryset = archive.values()

    def list(self, request, *args, **kwargs):
        queryset = list(archive.values())
        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def retrieve(self, request, pk=None, *args, **kwargs):
        # Note, archive[pk] will except if obj does not exist, .get(pk) returns None
        instance = archive.get(pk)
        serializer = search.serializers.AstroObjectRetrieve(instance=instance, many=False)
        return Response(serializer.data)

    # @list_route(url_name='filter-by-name', url_path='filter-by-name/(?P<name>[\w\d]+)')
    # def filter_by_name(self, request, name=None, *args, **kwargs):
    #     data = []
    #     for key, value in archive.items():
    #         if str(name) in str(value.name):
    #             # append to data
    #             data.append(value)
    #         elif str(name) in str(value.id):
    #             data.append(value)
    #
    #     completed_data = dict(enumerate(data))
    #     serializer = search.serializers.AvailableObjectRetrieve(instance=completed_data.values(), many=True)
    #     return Response(serializer.data)
    #
    # @list_route(url_name='filter-by-position',
    #             url_path='filter-by-position/' + hre.POSITION_RE.pattern)
    # def filter_by_position(self, request, position=None, *args, **kwargs):
    #     data = []
    #     print(position)
    #
    #     # pos_arr = position.split(',')
    #     # if pos_arr:
    #     #   print(pos_arr)
    #
    #     # for key, value in archive.items():
    #     #     if str(filter_term) in str(value.name):
    #     #         # append to data
    #     #         data.append(value)
    #     #     elif str(filter_term) in str(value.id):
    #     #         data.append(value)
    #     #
    #     # completed_data = dict(enumerate(data))
    #     # serializer = search.serializers.AvailableObjectRetrieve(instance=completed_data.values(), many=True)
    #     # return Response(serializer.data)
    #     return Response({})


FILTERBY_DOC_STRING = (r"""
    Filter objects in the DC archive by:

    keyword [id, name]:
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
            'urls': [reverse('search:filter-by', kwargs={"filter_term": "id"}, request=request),
                     reverse('search:filter-by', kwargs={"filter_term": "name"}, request=request),
                     reverse('search:filter-by', kwargs={"filter_term": "position"}, request=request)]
        })
FilterBy.__doc__ = FILTERBY_DOC_STRING


class FilterByTerm(generics.CreateAPIView):
    # Filter by a keyword or position
    queryset = archive.values()
    available_keywords = ['id', 'name']

    serializer_action_classes = {
        'id': search.serializers.FilterById,
        'name': search.serializers.FilterByName,
        'position': search.serializers.FilterByPosition,
    }

    def get_serializer_class(self):
        # Override the base method, using a different serializer
        # depending on the url parameter (serializer governs the fields
        # that are accessible to the route, form rendering, validation)
        filter_term = self.kwargs['filter_term']
        try:
            return self.serializer_action_classes[filter_term]
        except (KeyError, AttributeError):
            return super(FilterBy, self).get_serializer_class()

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

        c = SkyCoord(ra=ra, dec=dec, unit=(ra_unit, dec_unit))

        ra_deg = c.ra.degree
        dec_deg = c.dec.degree
        rad_deg = radius / (60 * 60)

        ra_min = ra_deg - rad_deg
        ra_max = ra_deg + rad_deg
        dec_min = dec_deg - rad_deg
        dec_max = dec_deg + rad_deg
        # print(_ra_deg, _dec_deg, _rad_deg)
        # print(_ra_min, _ra_max, _dec_min, _dec_max)
        data = []
        for key, x in archive.items():
            if (x.position['ra'] < ra_max) and (x.position['ra'] > ra_min) and \
                    (x.position['dec'] < dec_max) and (x.position['dec'] > dec_min):
                data.append(x)
        return data

    def filter_by_keyword(self, data=None, filter_term=None, search_value=None):
        filtered_list = []
        for key, value in data:
            if str(search_value) in str(getattr(value, filter_term)):
                filtered_list.append(value)
        return filtered_list

    def create(self, request, filter_term=None, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        if filter_term in self.available_keywords:
            _search_value = serializer.data.get(filter_term)
            data = self.filter_by_keyword(data=archive.items(), filter_term=filter_term, search_value=_search_value)

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
            serializer = search.serializers.AstroObjectList(page, many=True)
            return self.get_paginated_response(serializer.data)

        headers = self.get_success_headers(serializer.data)
        # return each as json using
        _serializer = search.serializers.AstroObjectRetrieve(instance=completed_data.values(), many=True)
        return Response(_serializer.data, status=status.HTTP_201_CREATED, headers=headers)
FilterByTerm.__doc__ = FILTERBY_DOC_STRING


class NameResolver(generics.CreateAPIView):
    """
    Return top match from NSV (Ned, then Simbad, then VizieR), returning the first likely result.
    """
    serializer_class = search.serializers.NameResolver
    queryset = archive.values()

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

