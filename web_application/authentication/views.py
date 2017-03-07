from django.contrib.auth.models import User
from rest_framework import generics, throttling

import restapi_app.exceptions
import restapi_app.renderers
import restapi_app.permissions

import authentication.serializer


class CreateUserView(generics.ListCreateAPIView):
    """
    Register a new user.
    """
    model = User
    permission_classes = [restapi_app.permissions.IsNotAuthenticated]
    serializer_class = authentication.serializer.CreateUserSerializer
    # throttle_classes = [throttling.AnonRateThrottle]

    def get_queryset(self):
        queryset = User.objects.none()
        return queryset
