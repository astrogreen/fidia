import json
import random
from pprint import pprint

from .models import (
    Query,
    GAMAPublic,
    Survey, SurveyMetaData,
    ReleaseType,
    Catalogue, CatalogueGroup,
    Image,
    Spectrum,
    TestFidiaSchema
)
from .serializers import (
    UserSerializer,
    QuerySerializerCreateUpdate, QuerySerializerList,
    GAMASerializer,

    SurveySerializer,
    ReleaseTypeSerializer,
    CatalogueSerializer, CatalogueGroupSerializer,
    ImageSerializer, SpectrumSerializer,
    AstroObjectSerializer_old,
    # manufacture_trait_serializer,
    # manufacture_galaxy_serializer_for_archive,
    # manufacture_trait_serializer_for_archive,
    SampleSerializer,
    AstroObjectSerializer,
    AstroObjectTraitSerializer,
    AstroObjectPropertyTraitSerializer
)

from .renderers import FITSRenderer

from . import AstroObject

from rest_framework import generics, permissions, renderers, views, viewsets, status, mixins
from rest_framework.decorators import api_view, detail_route, list_route
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework.renderers import TemplateHTMLRenderer
from rest_framework.generics import RetrieveAPIView
from rest_framework.exceptions import PermissionDenied
from rest_framework.settings import api_settings
from django.contrib.auth.models import User




# RESTFUL SQL QUERY DUMMY DATA
class QueryViewSet(viewsets.ModelViewSet):
    """
    This viewset automatically provides `list`, `create`, `retrieve`,
    `update` and `destroy` actions.
    """
    serializer_class = QuerySerializerList
    permission_classes = [permissions.IsAuthenticated]
    #  permission_classes = (permissions.IsAuthenticatedOrReadOnly,
    #                       IsOwnerOrReadOnly,)
    queryset = Query.objects.all()
  # base_name = 'query'

    def get_serializer_class(self):
        serializer_class = QuerySerializerList

        if self.request.method == 'GET':
            serializer_class = QuerySerializerList
        elif (self.request.method == 'POST') or (self.request.method == 'PUT'):
            serializer_class = QuerySerializerCreateUpdate

        return serializer_class

    def get_queryset(self):
        """
        This view should return a list of all thqueriests
        for the currently authenticated user.
        """
        user = self.request.user
        return Query.objects.filter(owner=user)


    def run_FIDIA(self, request, *args, **kwargs):
        #TODO ADD FIDIA(request.data['SQL'])
        dummyData = {"columns":["cataid","z","metal"],
               "index":  [random.randint(1,5),1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20],
               "data":   [[8823,0.0499100015,0.0163168724],
                          [63147,0.0499799997,0.0380015143],
                          [91963,0.0499899983,0.0106879927]]}
        for i in range(1):
            dummyData['data'].append([i,i,i])

        return dict(dummyData)


    def create(self, request, *args, **kwargs):
        """
        Create a model instance. Override CreateModelMixin create to catch the POST data for processing before save
        """
        #overwrite the post request data (don't forget to set mutable!!)
        saved_object = request.POST
        saved_object._mutable = True
        saved_object['queryResults'] = self.run_FIDIA(request.data)
        serializer = self.get_serializer(data=saved_object)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def perform_create(self, serializer):
        """
        Override CreateModelMixin perform_create to save object instance with ownership
        """
        serializer.save(owner=self.request.user)

    def update(self, request, *args, **kwargs):
        """
        Update a model instance.
        """
        partial = kwargs.pop('partial', False)
        instance = self.get_object()

        #current SQL
        saved_object = instance
        #inbound request
        incoming_object = self.request.data
        # pprint('- - - - NEW PUT - - - -')
        # print(json.loads(incoming_object['queryResults']))
        # pprint('- - - - end PUT - - - -')
        # testQueryResultsTamper=self.get_serializer(instance, data=incoming_object, partial=True)
        # testQueryResultsTamper.is_valid(raise_exception=True)
        #
        # pprint(testQueryResultsTamper.data['queryResults'])
        # pprint(saved_object.queryResults)

        #override the incoming queryResults with the saved version
        incoming_object['queryResults']=(saved_object.queryResults)

        # if new sql (and/or results have been tampered with), re-run fidia and override results
        # if (incoming_object['SQL'] != saved_object.SQL) or (testQueryResultsTamper.data['queryResults'] != saved_object.queryResults):
        if incoming_object['SQL'] != saved_object.SQL:
            pprint('sql or qR changed')

            # if (testQueryResultsTamper.data['queryResults'] != saved_object.queryResults):
            #     pprint('qR changed')
            #     raise PermissionDenied(detail="WARNING - editing the query result is forbidden. Editable fields: title, SQL.")

            incoming_object['queryResults'] = self.run_FIDIA(self.request.data)
            pprint('update object')

        serializer = self.get_serializer(instance, data=incoming_object, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)

    def perform_update(self, serializer):
        serializer.save()

    def partial_update(self, request, *args, **kwargs):
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)

class UserViewSet(viewsets.ReadOnlyModelViewSet):
    """
    This viewset automatically provides `list` and `detail` actions.
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAdminUser]


#SOV TESTS
class SOVViewSet(viewsets.ModelViewSet):
    """
    A simple ViewSet for viewing and editing GAMA obj.
    """
    queryset = GAMAPublic.objects.all()
    serializer_class = GAMASerializer
    permission_classes = [permissions.AllowAny]
    # template_name = 'restapi_app/sov/gama-sov.html'

    #not possible to handle json fields with uploader, just write in from backend here:
    def get_InputCatA(self, request, *args, **kwargs):
        dummyInputCatA = {
            "CATAID":550649,
            "OBJID":588848899356819700,
            "RA":136.63311629612,
            "DEC":-0.524177203137492,
            "FLAGS":68988047632,
            "PRIMTARGET":0,
            "PETRORAD_R":4.20203,
            "PSFMAG_R":19.0331,
            "FIBERMAG_R":19.0405,
            "FLAGS_R":6755674587562000,
            "EXTINCTION_R":0.0829252,
            "PETROR90_R":5.16121,
            "PETROR50_R":1.83143,
            "PETROMAG_U":20.9959,
            "PETROMAG_G":18.9612,
            "PETROMAG_R":17.9187,
            "PETROMAG_I":17.4159,
            "PETROMAG_Z":17.1031,
            "MODELMAG_U":21.1705,
            "MODELMAG_G":18.9437,
            "MODELMAG_R":17.8006,
            "MODELMAG_I":17.297,
            "MODELMAG_Z":16.9011,
            "STATUS":9843,
            "RUN":756
          }
        return dict(dummyInputCatA)

    def get_TilingCat(self, request, *args, **kwargs):
        dummyTilingCat = {
            "CATAID":550649,
            "OBJID":588848899356819700,
            "RA":136.63311629612,
            "DEC":-0.524177203137492,
            "FIBERMAG_R":19.0405,
            "R_PETRO":17.8358,
            "U_MODEL":21.0151,
            "G_MODEL":18.8293,
            "R_MODEL":17.7177,
            "I_MODEL":17.2341,
            "Z_MODEL":16.8565,
            "SURVEY_CODE":5,
            "Z":0.156059995293617,
            "NQ":4,
            "SPECID":"G09_Y1_FS2_052",
            "NUM_GAMA_SPEC":1,
            "R_SB":21.1452,
            "SG_SEP":1.23254,
            "SG_SEP_JK":0.484925,
            "K_AUTO":16.5763,
            "TARGET_FLAGS":124,
            "SURVEY_CLASS":7,
            "PRIORITY_CLASS":3,
            "NEIGHBOUR_CLASS":1,
            "MASK_IC_10":0,
            "MASK_IC_12":0,
            "VIS_CLASS":0,
            "VIS_CLASS_USER":"xxx",
            "DR2_FLAG":1
        }
        return dict(dummyTilingCat)

    def get_SpecAll(self, request, *args, **kwargs):
        dummySpecAll = {
             "SPECID":"G09_Y1_FS2_052",
            "SURVEY":"GAMA",
            "SURVEY_CODE":5,
            "RA":136.63308,
            "DEC":-0.52418,
            "WMIN":3727.79,
            "WMAX":8856.74,
            "Z":0.15606,
            "NQ":4,
            "PROB":0.963,
            "FILENAME":"/GAMA/dr2/data/spectra/gama/reduced_08/1d/G09_Y1_FS2_052.fit",
            "URL":"http://www.gama-survey.org/dr2/data/spectra/gama/reduced_08/1d/G09_Y1_FS2_052.fit",
            "URL_IMG":"http://www.gama-survey.org/dr2/data/spectra/gama/reduced_08/1d/png/G09_Y1_FS2_052.png",
            "CATAID":550649,
            "GAMA_NAME":"GAMAJ090631.94-003127.0",
            "IC_FLAG":3,
            "DIST":0.14,
            "IS_SBEST":1,
            "IS_BEST":1
        }
        return dict(dummySpecAll)

    def get_SersicCat(self,request, *args, **kwargs):
        dummySersicCat = {
            "CATAID":550649,
            "RA":136.6331,
            "DEC":-0.5241772,
            "SIGMA_INDEX":118530,
            "OBJNAME":"S00118530",
            "FILENAME":"/GAMA/dr2/data/imaging/gama/SersicPhotometry/v07/S00118530/",
            "URL":"http://www.gama-survey.org/dr2/data/imaging/gama/SersicPhotometry/v07/S00118530/",
            "URL_R":"http://www.gama-survey.org/dr2/data/imaging/gama/SersicPhotometry/v07/S00118530/prfplot_sdss_r_g09_S00118530.png",
            "URL_K":"http://www.gama-survey.org/dr2/data/imaging/gama/SersicPhotometry/v07/S00118530/prfplot_ukidss_K_g09_S00118530.png",
            "PSF_FWHM_U":1.47804,
            "GAL_CHI2_U":1.075,
            "GAL_RA_U":136.633124035423,
            "GAL_DEC_U":-0.524217019696594,
            "GAL_XCEN_U":600.5309,
            "GAL_YCEN_U":600.2963,
            "GAL_MAG_U":20.885,
            "GAL_MAG_10RE_U":20.885,
            "GAL_MU_0_U":23.6964608346939,
            "GAL_MU_E_U":24.746098336,
            "GAL_MU_E_AVG_U":24.2472756918573,
            "GAL_RE_U":2.4019167,
            "GAL_R90_U":4.71635678299877,
            "GAL_RE_C_U":1.87657187981548,
            "GAL_INDEX_U":0.6402,
            "GAL_ELLIP_U":0.3896,
            "GAL_PA_U":58.2406,
            "PSF_FWHM_G":1.29837,
            "GAL_CHI2_G":0.967,
            "GAL_RA_G":136.633120878587,
            "GAL_DEC_G":-0.5241750913979,
            "GAL_XCEN_G":600.5645,
            "GAL_YCEN_G":600.7418,
            "GAL_MAG_G":18.7335,
            "GAL_MAG_10RE_G":18.7659546297431,
            "GAL_MU_0_G":16.5194052238747,
            "GAL_MU_E_G":23.9295215875833,
            "GAL_MU_E_AVG_G":22.594894986374,
            "GAL_RE_G":2.4609705,
            "GAL_R90_G":12.4021934664146,
            "GAL_RE_C_G":2.36150605300137,
            "GAL_INDEX_G":3.5777,
            "GAL_ELLIP_G":0.0792,
            "GAL_PA_G":84.3658,
            "PSF_FWHM_R":1.21701,
            "GAL_CHI2_R":0.985,
            "GAL_RA_R":136.633118554894,
            "GAL_DEC_R":-0.524170762582158,
            "GAL_XCEN_R":600.5892,
            "GAL_YCEN_R":600.7878,
            "GAL_MAG_R":17.6222,
            "GAL_MAG_10RE_R":17.6696593296026,
            "GAL_MU_0_R":14.086032952175,
            "GAL_MU_E_R":22.8387209770795,
            "GAL_MU_E_AVG_R":21.4206639920672,
            "GAL_RE_R":2.3098104,
            "GAL_R90_R":13.3818852825987,
            "GAL_RE_C_R":2.29404992020803,
            "GAL_INDEX_R":4.1962,
            "GAL_ELLIP_R":0.01359999999,
            "GAL_PA_R":117.9664,
            "PSF_FWHM_I":1.28142,
            "GAL_CHI2_I":1.021,
            "GAL_RA_I":136.633117266399,
            "GAL_DEC_I":-0.52416526646805,
            "GAL_XCEN_I":600.6029,
            "GAL_YCEN_I":600.8462,
            "GAL_MAG_I":17.2837,
            "GAL_MAG_10RE_I":17.3166426303378,
            "GAL_MU_0_I":14.4321047115313,
            "GAL_MU_E_I":21.8869344809512,
            "GAL_MU_E_AVG_I":20.5493129032653,
            "GAL_RE_I":1.8234471,
            "GAL_R90_I":9.2337781457466,
            "GAL_RE_C_I":1.7948685443353,
            "GAL_INDEX_I":3.5983,
            "GAL_ELLIP_I":0.0311,
            "GAL_PA_I":129.7839,
            "PSF_FWHM_Z":1.2204,
            "GAL_CHI2_Z":1.023,
            "GAL_RA_Z":136.633115035237,
            "GAL_DEC_Z":-0.524174565750861,
            "GAL_XCEN_Z":600.6266,
            "GAL_YCEN_Z":600.7474,
            "GAL_MAG_Z":17.007,
            "GAL_MAG_10RE_Z":17.038378774342,
            "GAL_MU_0_Z":13.9961787831643,
            "GAL_MU_E_Z":21.3073187218819,
            "GAL_MU_E_AVG_Z":19.9793810191473,
            "GAL_RE_Z":1.6335732,
            "GAL_R90_Z":8.14468663555043,
            "GAL_RE_C_Z":1.56814518775438,
            "GAL_INDEX_Z":3.5321,
            "GAL_ELLIP_Z":0.0785,
            "GAL_PA_Z":144.476,
            "PSF_FWHM_Y":0.78987,
            "GAL_CHI2_Y":1.093,
            "GAL_RA_Y":136.633108043864,
            "GAL_DEC_Y":-0.524174416847737,
            "GAL_XCEN_Y":600.7009,
            "GAL_YCEN_Y":600.749,
            "GAL_MAG_Y":16.8879,
            "GAL_MAG_10RE_Y":16.9279950869551,
            "GAL_MU_0_Y":12.8349081654787,
            "GAL_MU_E_Y":20.9350667949526,
            "GAL_MU_E_AVG_Y":19.5559632675568,
            "GAL_RE_Y":1.4517336,
            "GAL_R90_Y":7.87008247198937,
            "GAL_RE_C_Y":1.36308431163933,
            "GAL_INDEX_Y":3.8956,
            "GAL_ELLIP_Y":0.1184,
            "GAL_PA_Y":106.2277,
            "PSF_FWHM_J":0.7119,
            "GAL_CHI2_J":1.12,
            "GAL_RA_J":136.633117575398,
            "GAL_DEC_J":-0.524178508635354,
            "GAL_XCEN_J":600.5996,
            "GAL_YCEN_J":600.7055,
            "GAL_MAG_J":16.6056,
            "GAL_MAG_10RE_J":16.6602338295418,
            "GAL_MU_0_J":11.5027799171682,
            "GAL_MU_E_J":20.8874036737778,
            "GAL_MU_E_AVG_J":19.4341109191598,
            "GAL_RE_J":1.5423822,
            "GAL_R90_J":9.50898075151555,
            "GAL_RE_C_J":1.46761536418228,
            "GAL_INDEX_J":4.4873,
            "GAL_ELLIP_J":0.0946,
            "GAL_PA_J":62.7543,
            "PSF_FWHM_H":0.68817,
            "GAL_CHI2_H":1.159,
            "GAL_RA_H":136.633118968563,
            "GAL_DEC_H":-0.524173868338792,
            "GAL_XCEN_H":600.5848,
            "GAL_YCEN_H":600.7548,
            "GAL_MAG_H":16.4021,
            "GAL_MAG_10RE_H":16.4580863881885,
            "GAL_MU_0_H":10.9732797889069,
            "GAL_MU_E_H":20.4770861366708,
            "GAL_MU_E_AVG_H":19.0173966766146,
            "GAL_RE_H":1.3891881,
            "GAL_R90_H":8.66361970188087,
            "GAL_RE_C_H":1.33036068215851,
            "GAL_INDEX_H":4.5422,
            "GAL_ELLIP_H":0.0829,
            "GAL_PA_H":83.0372,
            "PSF_FWHM_K":0.71529,
            "GAL_CHI2_K":1.08,
            "GAL_RA_K":136.633116982475,
            "GAL_DEC_K":-0.524179487593464,
            "GAL_XCEN_K":600.6059,
            "GAL_YCEN_K":600.6951,
            "GAL_MAG_K":16.3303,
            "GAL_MAG_10RE_K":16.3896958143743,
            "GAL_MU_0_K":10.8435874959086,
            "GAL_MU_E_K":20.6482844213082,
            "GAL_MU_E_AVG_K":19.1727730900085,
            "GAL_RE_K":1.5237372,
            "GAL_R90_K":9.77988436213722,
            "GAL_RE_C_K":1.4770822654367,
            "GAL_INDEX_K":4.6808,
            "GAL_ELLIP_K":0.0603,
            "GAL_PA_K":151.8129
          }
        return dict(dummySersicCat)

    def create(self, request, *args, **kwargs):
        """
        Create a model instance. Override CreateModelMixin create to catch the POST data for processing before save
        """
        #overwrite the post request data (don't forget to set mutable!!)
        saved_object = request.POST
        saved_object._mutable = True
        saved_object['InputCatA'] = self.get_InputCatA(self.request)
        saved_object['TilingCat'] = self.get_TilingCat(self.request)
        saved_object['SpecAll'] = self.get_SpecAll(self.request)
        saved_object['SersicCat'] = self.get_SersicCat(self.request)
        serializer = self.get_serializer(data=saved_object)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)
        # , template_name='restapi_app/sov/gama-sov.html')


#DATAMODEL TESTS
class SurveyViewSet(viewsets.ModelViewSet):
    """
    This viewset automatically provides `list` and `detail` actions.
    """
    queryset = Survey.objects.all()
    serializer_class = SurveySerializer
    permission_classes = [permissions.AllowAny]
    lookup_field = 'title'

class ReleaseTypeViewSet(viewsets.ModelViewSet):
    """
    This viewset automatically provides `list` and `detail` actions.
    """
    queryset = ReleaseType.objects.all()
    serializer_class = ReleaseTypeSerializer
    permission_classes = [permissions.AllowAny]
    lookup_field = 'slugField'

class CatalogueViewSet(viewsets.ModelViewSet):
    """
    This viewset automatically provides `list` and `detail` actions.
    """
    queryset = Catalogue.objects.all()
    serializer_class = CatalogueSerializer
    permission_classes = [permissions.AllowAny]
    lookup_field = 'slugField'

class CatalogueGroupViewSet(viewsets.ModelViewSet):
    """
    This viewset automatically provides `list` and `detail` actions.
    """
    queryset = CatalogueGroup.objects.all()
    serializer_class = CatalogueGroupSerializer
    permission_classes = [permissions.AllowAny]
    lookup_field = 'slugField'

class ImageViewSet(viewsets.ModelViewSet):
    """
    This viewset automatically provides `list` and `detail` actions.
    """
    queryset = Image.objects.all()
    serializer_class = ImageSerializer
    permission_classes = [permissions.AllowAny]
    lookup_field = 'slugField'

class SpectraViewSet(viewsets.ModelViewSet):
    """
    This viewset automatically provides `list` and `detail` actions.
    """
    queryset = Spectrum.objects.all()
    serializer_class = SpectrumSerializer
    permission_classes = [permissions.AllowAny]
    lookup_field = 'slugField'


# NON-MODEL ENDPOINTS
class CustomGet(views.APIView):
    """
    A custom endpoint for GET request.
    """
    def get(self, request, format=None):
        """
        Return a hardcoded response.
        """
        return Response({"success": True, "content": "DATA!"})

class FIDIA(object):

    def __init__(self, astroobject, trait, version, *args, **kwargs):
        # Initialize any variables necessary from input
        self.astroobject = astroobject
        self.trait = trait
        self.version = version

    def do_work(self):
        result = {'astroobject':self.astroobject, 'trait': self.trait, 'version': self.version, 'endpoint-content': 'a random string'};
        return result

class ModelFreeView(views.APIView):
    """
    ModelFreeView in restapp_app/views.py

    This model-independent view allows for custom parameters in the url.
    Currently set to three levels, but multiple nesting depths can be added very easily in the
    urls.py file. Try:
    e.g., http://127.0.0.1:8000/asvo/model-free/resource/gal/redshift/v1
    e.g., http://127.0.0.1:8000/asvo/model-free/resource/gal/redshift/v1/?format=json
    e.g., http://127.0.0.1:8000/asvo/model-free/resource/gal/redshift/v1/?format=csv

    - Serialization of results needs consideration - depending on type
    - Permissions can be plugged in to the entire view, but unclear as
    to how per-object permissions would work.
    - allows all endpoints, but no info about data model
    - schema?

    """
    #can add in custom permissions from permissions.py file here
    permission_classes = (permissions.AllowAny,)


    def get(self, request, *args, **kwargs):
        # Process params from request
        get_arg1 = self.kwargs['arg1']
        get_arg2 = self.kwargs['arg2']
        get_arg3 = self.kwargs['arg3']

        # Any URL parameters gets passed in **kwargs
        myObject = FIDIA(get_arg1, get_arg2, get_arg3, *args, **kwargs)
        result = myObject.do_work()
        response = Response(result, status=status.HTTP_200_OK)
        return response

class ModelFreeView(views.APIView):
    """
    ModelFreeView in restapp_app/views.py

    This model-independent view allows for custom parameters in the url.

    Using the APIView class, rather than hooking up a Viewset

    Currently set to three levels, but multiple nesting depths can be added very easily in the
    urls.py file. Try:
    e.g., http://127.0.0.1:8000/asvo/model-free/resource/gal/redshift/v1
    e.g., http://127.0.0.1:8000/asvo/model-free/resource/gal/redshift/v1/?format=json
    e.g., http://127.0.0.1:8000/asvo/model-free/resource/gal/redshift/v1/?format=csv

    - Serialization of results needs consideration
    - Permissions can be plugged in to the entire view, but unclear as
    to how per-object permissions would work.
    - allows all endpoints, but no info about data model
    - schema?

    """
    #can add in custom permissions from permissions.py file here
    permission_classes = (permissions.AllowAny,)


    def get(self, request, *args, **kwargs):
        # Process params from request
        get_arg1 = self.kwargs['arg1']
        get_arg2 = self.kwargs['arg2']
        get_arg3 = self.kwargs['arg3']

        # Any URL parameters gets passed in **kwargs
        myObject = FIDIA(get_arg1, get_arg2, get_arg3, *args, **kwargs)
        result = myObject.do_work()
        response = Response(result, status=status.HTTP_200_OK)
        return response


# NON-MODEL ENDPOINTS (using VIEWSETS)

# Expose an AstroObject resource (here pure python object)
# (see __init__.py)

# create dict of AstroObjects for now
# using HBase store, some caching system, LDAP, some files..
# The API will perform the usual CRUD operations on items in the list

astroobjects = {
    1: AstroObject(id=1, asvoid='0000000001', gamacataid='G65406', redshift='0.02', spectrum='.fits'),
    2: AstroObject(id=2, asvoid='0000000002', gamacataid='G65404', samiid='SAMI001', redshift='0.01', spectrum='.fits'),
    3: AstroObject(id=3, asvoid='0000000003', samiid='SAMIGAL', redshift='0.03', spectrum=None),
}

def get_next_astobj_id():
    return max(astroobjects) + 1

class AstroObjectViewSet(viewsets.ViewSet):
    serializer_class = AstroObjectSerializer
    # required for browsable API to render handy form

    def list(self, request):
        serializer = AstroObjectSerializer(
            instance = astroobjects.values(), many=True
        )
        return Response(serializer.data)

    def create(self, request):
        serializer = AstroObjectSerializer(data=request.data)
        if serializer.is_valid():
            astroobj = serializer.save()
            astroobj.id = get_next_astobj_id()
            astroobjects[astroobj.id] = astroobj
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


    def retrieve(self, request, pk=None):
        try:
            astroobject = astroobjects[int(pk)]
        except KeyError:
            return Response(status=status.HTTP_404_NOT_FOUND)
        except ValueError:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        serializer = AstroObjectSerializer(instance=astroobject)
        return Response(serializer.data)


    def update(self, request, pk=None):
        try:
            astroobject = astroobjects[int(pk)]
        except KeyError:
            return Response(status=status.HTTP_404_NOT_FOUND)
        except ValueError:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        serializer = AstroObjectSerializer(
            data=request.data, instance=astroobject)
        if serializer.is_valid():
            astroobject = serializer.save()
            astroobjects[astroobject.id] = astroobject
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


    def partial_update(self, request, pk=None):
        try:
            astroobject = astroobjects[int(pk)]
        except KeyError:
            return Response(status=status.HTTP_404_NOT_FOUND)
        except ValueError:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        serializer = AstroObjectSerializer(
            data=request.data,
            instance=astroobject,
            partial=True)
        if serializer.is_valid():
            astroobject = serializer.save()
            astroobjects[astroobject.id] = astroobject
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


    def destroy(self, request, pk=None):
        try:
            astroobject = astroobjects[int(pk)]
        except KeyError:
            return Response(status=status.HTTP_404_NOT_FOUND)
        except ValueError:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        del astroobjects[astroobject.id]
        return Response(status=status.HTTP_204_NO_CONTENT)



# ASVO:

from fidia.archive.test_archive import ExampleArchive

ar = ExampleArchive()
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


class SampleViewSet(mixins.ListModelMixin,
                    viewsets.GenericViewSet):
    def list(self,request, pk=None, sample_pk=None, format=None):
        try:
            astroobject = sample
        except KeyError:
            return Response(status=status.HTTP_404_NOT_FOUND)
        except ValueError:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        serializer_class = SampleSerializer
        serializer = serializer_class(
            instance=astroobject, many=False,
            context={'request':request}
        )
        return Response(serializer.data)


class GalaxyViewSet(mixins.ListModelMixin,
                    viewsets.GenericViewSet):
    def list(self, request, pk=None, sample_pk=None, galaxy_pk=None, format=None):
        try:
            astroobject = sample[galaxy_pk]
        except KeyError:
            return Response(status=status.HTTP_404_NOT_FOUND)
        except ValueError:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        serializer_class = AstroObjectSerializer
        serializer = serializer_class(
            instance=astroobject, many=False,
            context={'request':request}
        )
        return Response(serializer.data)


class TraitViewSet(mixins.ListModelMixin,
                    viewsets.GenericViewSet):
    def list(self, request, pk=None, sample_pk=None, galaxy_pk=None, trait_pk=None, format=None):
        try:
            astroobject = sample[galaxy_pk][trait_pk]
        except KeyError:
            return Response(status=status.HTTP_404_NOT_FOUND)
        except ValueError:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        serializer_class = AstroObjectTraitSerializer
        serializer = serializer_class(
            instance = astroobject, many=False,
            context={'request': request}
        )
        return Response(serializer.data)


class TraitPropertyViewSet(mixins.ListModelMixin,
                            viewsets.GenericViewSet):
    def list(self, request, pk=None, sample_pk=None, galaxy_pk=None, trait_pk=None, traitproperty_pk=None, format=None):
        try:
            # address trait properties via . not []
            astroobject = getattr(sample[galaxy_pk][trait_pk],traitproperty_pk)
        except KeyError:
            return Response(status=status.HTTP_404_NOT_FOUND)
        except ValueError:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        serializer_class = AstroObjectPropertyTraitSerializer
        serializer = serializer_class(
            instance=astroobject, many=False,
            context={'request': request}
        )
        return Response(serializer.data)