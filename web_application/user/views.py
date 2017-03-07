import random, collections, logging
from django.contrib.auth.models import User
from django.http.response import HttpResponseRedirect
from django.contrib.auth import authenticate, login

from rest_framework import generics, permissions, renderers, mixins, views, viewsets, status, mixins, exceptions, throttling
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework.settings import api_settings

import restapi_app.exceptions
import restapi_app.renderers
import restapi_app.permissions

import user.serializer
import user.exceptions
import user.models


class UserProfileView(generics.RetrieveUpdateDestroyAPIView):
    """
    USER PROFILE (restful instance allowing user to update details)
    Retrieve/Update/Destroy a user instance (must be authenticated and username=user)
    Users cannot change their username
    """
    serializer_class = user.serializer.UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'username'

    def get_queryset(self):
        """
        Return User info for currently authenticated user
        """
        username = self.request.user
        return User.objects.filter(username=username)


class UserViewSet(viewsets.ReadOnlyModelViewSet):
    """
    If Admin, view all users at this route
    If not, view only user detail
    """
    queryset = User.objects.all()
    serializer_class = user.serializer.UserSerializer
    permission_classes = [permissions.IsAdminUser]

