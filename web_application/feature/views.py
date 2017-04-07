from django.shortcuts import render
import random, collections, logging
import json

import restapi_app.exceptions
import sys

import feature.models
import feature.serializers

from rest_framework import generics, permissions, renderers, mixins, views, viewsets, status, mixins, exceptions


# Create your views here.
class Feature(viewsets.ModelViewSet):
    """
    Create, update and destroy queries
    """
    serializer_class = feature.serializers.FeatureSerializer
    # permission_classes = [permissions.IsAuthenticated]
    pagination_class = None
    queryset = feature.models.Feature.objects.all()

    # def get_queryset(self):
    #     """
    #     Return a list of all queries for the currently authenticated user.
    #     """
    #     user = self.request.user
    #     return query.models.Query.objects.filter(owner=user).order_by('-updated')
    #
    # def perform_create(self, serializer):
    #     """
    #     Override CreateModelMixin perform_create to save object instance with ownership
    #     """
    #     serializer.save(owner=self.request.user)
