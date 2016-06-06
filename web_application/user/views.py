import random, collections, logging
from django.contrib.auth.models import User

from rest_framework import generics, permissions, renderers, mixins, views, viewsets, status, mixins, exceptions

import restapi_app.exceptions
import restapi_app.renderers
import restapi_app.permissions

import user.serializer


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
    This viewset automatically provides `list` and `detail` actions.
    """
    queryset = User.objects.all()
    serializer_class = user.serializer.UserSerializer
    permission_classes = [permissions.IsAdminUser]
