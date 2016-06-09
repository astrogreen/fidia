import random, collections, logging
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404, redirect
from rest_framework import generics, permissions, renderers, mixins, views, viewsets, status, mixins, exceptions, reverse
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


class ChangePasswordView(views.APIView):
    renderer_classes = [renderers.TemplateHTMLRenderer]
    template_name = 'user/password/password_change.html'

    def get(self, request):
        unbound_user_instance = User()
        serializer = user.serializer.UserPasswordChangeSerializer(unbound_user_instance)
        return Response({'serializer': serializer, 'user': unbound_user_instance})

    def post(self, request):
        # check username and email in request data (assign to data as request.data is immutable)
        data = request.data.copy()
        try:
            username = data['username']
            email = data['email']
        except KeyError:
                return Response(status=status.HTTP_404_NOT_FOUND)
        except ValueError:
                return Response(status=status.HTTP_400_BAD_REQUEST)

        # Get associated user instance
        if User.objects.filter(username=username).exists():
            # user_instance = User.objects.filter(username=username, email=email)
            user_instance = User.objects.get(username=username)
            # Make sure the email submitted is the same as in db
            if user_instance.email == email:
                # pop off the confirm_password field, raise exception if not equal
                confirm_password = data.pop('confirm_password')[0]

                if data['password'] != confirm_password:
                    raise restapi_app.exceptions.CustomValidation("Passwords do not match", 'detail', 404)

                print('match')
                # Only pass the new password to the serializer (no danger of overriding username/email combo)

                print(data)

                serializer = user.serializer.UserPasswordChangeSerializer(user_instance, data=data, partial=True)
                print(serializer)

                serializer.is_valid(raise_exception=True)
                print('serializerisvalid?', serializer.is_valid())

                if not serializer.is_valid():
                    print('return not valid')
                    # if not valid, return form bound with submitted data TODO make useful to the user
                    return Response({'serializer': serializer, 'user': user})
                # Valid - go ahead and update (TODO WRITE THIS METHOD ON SERIALIZER)
                # serializer.update()
                self.perform_update(serializer)
                return Response(serializer.data)
                # return redirect(reverse.reverse('rest_framework:login'))
            else:
                raise restapi_app.exceptions.Conflict('Email %s is not associated with User %s' % (username, email))
        else:
            raise restapi_app.exceptions.CustomValidation("Username not found", 'detail', 404)

    def perform_update(self, serializer):
        serializer.save()

