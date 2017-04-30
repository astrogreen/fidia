from django.shortcuts import render
from rest_framework import generics, permissions, renderers, mixins, views, viewsets, status, mixins, exceptions
import support.models
import support.serializers


class Contact(viewsets.GenericViewSet, mixins.CreateModelMixin, mixins.ListModelMixin):
    permissions = [permissions.IsAuthenticated]
    serializer_class = support.serializers.ContactSerializer
    queryset = support.models.Contact.objects.none()
