from collections import OrderedDict
import requests
from operator import itemgetter, attrgetter
# from rest_framework.decorators import detail_route, list_route
from rest_framework import generics, permissions, renderers, mixins, views, viewsets, status, mixins, exceptions, renderers
from rest_framework.response import Response

import xml.etree.ElementTree as ET

from astropy import units as unit
from astropy.coordinates import SkyCoord

import search.serializers
from search.helpers.dummy_positions import DUMMY_POSITIONS

# def filterbyvalue(seq, value):
#     for el in seq:
#         if el.attribute == value: yield el


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


class FilterByName(generics.CreateAPIView):
    """
    Return only objects in the DC archive whose name includes some string.
    /asvo/filter-by-name/
    """
    serializer_class = search.serializers.FilterByName
    queryset = archive.values()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = []
        __name = serializer.data.get('name')
        for key, value in archive.items():
            if str(__name) in str(value.name):
                # append to data
                data.append(value)

        completed_data = dict(enumerate(data))
        page = self.paginate_queryset(list(completed_data.values()))

        if page is not None:
            serializer = search.serializers.AstroObjectList(page, many=True)
            return self.get_paginated_response(serializer.data)

        headers = self.get_success_headers(serializer.data)
        _serializer = search.serializers.AstroObjectRetrieve(instance=completed_data.values(), many=True)
        return Response(_serializer.data, status=status.HTTP_201_CREATED, headers=headers)


class FilterById(generics.CreateAPIView):
    """
    Return only objects in the DC archive whose name includes some string.
    /asvo/filter-by-id/
    """
    serializer_class = search.serializers.FilterById
    queryset = archive.values()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = []
        _id = serializer.data.get('id')
        for key, value in archive.items():
            if str(_id) in str(value.id):
                # append to data
                data.append(value)

        completed_data = dict(enumerate(data))
        page = self.paginate_queryset(list(completed_data.values()))

        if page is not None:
            serializer = search.serializers.AstroObjectList(page, many=True)
            return self.get_paginated_response(serializer.data)

        headers = self.get_success_headers(serializer.data)
        # return each as json using
        _serializer = search.serializers.AstroObjectRetrieve(instance=completed_data.values(), many=True)
        return Response(_serializer.data, status=status.HTTP_201_CREATED, headers=headers)


class FilterByPosition(generics.CreateAPIView):
    """
    Radius optional (default 3arcsec)
    position: 
     Returns top X
     Accepts ra,dec (sexidecimal or deg) position.
        valid formats:
        01:12:02.23,+49:28:35.0
        018.0093158, +49.4763969
     /asvo/filter-by-position/
    """
    serializer_class = search.serializers.FilterByPosition
    queryset = archive.values()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        _ra = serializer.data.get('ra')
        _dec = serializer.data.get('dec')
        _radius = serializer.data.get('radius')

        # sniff out unit type
        _ra_unit = unit.deg
        _dec_unit = unit.deg
        if ':' in _ra:
            _ra_unit = unit.hourangle
        if ':' in _dec:
            _dec_unit = unit.hourangle

        c = SkyCoord(ra=_ra, dec=_dec, unit=(_ra_unit, _dec_unit))

        _ra_deg = c.ra.degree
        _dec_deg = c.dec.degree
        _rad_deg = _radius/(60*60)

        _ra_min = _ra_deg - _rad_deg
        _ra_max = _ra_deg + _rad_deg
        _dec_min = _dec_deg - _rad_deg
        _dec_max = _dec_deg + _rad_deg
        # print(_ra_deg, _dec_deg, _rad_deg)
        # print(_ra_min, _ra_max, _dec_min, _dec_max)
        data = []
        for key, x in archive.items():
            if (x.position['ra'] < _ra_max) and (x.position['ra'] > _ra_min) and (x.position['dec'] < _dec_max) and (x.position['dec'] > _dec_min):
                # append to data
                data.append(x)

        completed_data = dict(enumerate(data))
        page = self.paginate_queryset(list(completed_data.values()))

        if page is not None:
            serializer = search.serializers.AstroObjectList(page, many=True)
            return self.get_paginated_response(serializer.data)

        headers = self.get_success_headers(serializer.data)
        _serializer = search.serializers.AstroObjectRetrieve(instance=completed_data.values(), many=True)
        return Response(_serializer.data, status=status.HTTP_201_CREATED, headers=headers)


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

