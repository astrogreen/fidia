import json
import random
from pprint import pprint

from restapi_app.models import Query, Survey, Version, Product
from restapi_app.serializers import (
    UserSerializer,
    QuerySerializerCreateUpdate, QuerySerializerList,
    SurveySerializer, VersionSerializer
)

from rest_framework import generics, permissions, renderers, viewsets, status, mixins
from rest_framework.decorators import api_view, detail_route, list_route
from rest_framework.response import Response
from rest_framework.reverse import reverse

from rest_framework.exceptions import PermissionDenied
from rest_framework.settings import api_settings
from django.contrib.auth.models import User

# from snippets.permissions import IsOwnerOrReadOnl

from rest_framework_extensions.mixins import NestedViewSetMixin



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







#TESTING NESTED ROUTES
class SurveyViewSet(NestedViewSetMixin, viewsets.ModelViewSet):
    """
    This viewset automatically provides `list` and `detail` actions.
    """
    queryset = Survey.objects.all()
    serializer_class = SurveySerializer
    permission_classes = [permissions.AllowAny]


class VersionViewSet(NestedViewSetMixin, viewsets.ModelViewSet):
    """
    This viewset automatically provides `list` and `detail` actions.
    """
    queryset = Version.objects.all()
    serializer_class = VersionSerializer
    permission_classes = [permissions.AllowAny]
