from django.contrib.auth.models import User
from rest_framework import generics, throttling
from django.conf import settings
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

    # Apply anon rate throttle
    # Limits the rate of API calls that may be made by a anonymous users.
    # The IP address of the request will be used as the unique cache key.

    if not settings.DEBUG:
        throttle_classes = [throttling.AnonRateThrottle]

    def get_queryset(self):
        queryset = User.objects.none()
        return queryset
