from django.contrib.auth.models import User

from rest_framework import generics, permissions, viewsets

import user.serializer
import user.models


class UserProfileView(generics.RetrieveUpdateDestroyAPIView):
    """
    USER PROFILE
    Retrieve/Update/Destroy a user instance (must be authenticated)
    Users cannot change their username
    """
    serializer_class = user.serializer.UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'username'

    def get_serializer(self, *args, **kwargs):
        kwargs['partial'] = True
        return super(UserProfileView, self).get_serializer(*args, **kwargs)

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

