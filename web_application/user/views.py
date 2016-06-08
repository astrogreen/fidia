import random, collections, logging
from django.contrib.auth.models import User

from rest_framework import generics, permissions, renderers, mixins, views, viewsets, status, mixins, exceptions
from rest_framework.response import Response

import restapi_app.exceptions
import restapi_app.renderers
import restapi_app.permissions

import user.serializer
import user.models


class CreateUserView(generics.ListCreateAPIView):
    """
    User View to allow registration
    """
    model = User
    permission_classes = [restapi_app.permissions.IsNotAuthenticated]
    serializer_class = user.serializer.CreateUserSerializer

    class CreateUserRenderer(restapi_app.renderers.ExtendBrowsableAPIRenderer):
        template = 'user/register/register.html'

    renderer_classes = [CreateUserRenderer, renderers.JSONRenderer]

    def get_queryset(self):
        queryset = User.objects.none()
        return queryset


class UserViewSet(viewsets.ReadOnlyModelViewSet):
    """
    If Admin, view all users at this route
    If not, view only user detail
    """
    queryset = User.objects.all()
    serializer_class = user.serializer.UserSerializer
    permission_classes = [permissions.IsAdminUser]


class UserProfileView(generics.RetrieveUpdateDestroyAPIView):
    """
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
        user = self.request.user
        return User.objects.filter(username=user)



