import random, collections, logging
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404, redirect


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
import user.renderers


# class CreateUserView(generics.ListCreateAPIView):
#     """
#     User View to allow registration
#     Throttle by IP to twice a day?
#     """
#     model = User
#     permission_classes = [restapi_app.permissions.IsNotAuthenticated]
#     serializer_class = user.serializer.CreateUserSerializer
#     # throttle_classes = [throttling.AnonRateThrottle]
#
#     class CreateUserRenderer(restapi_app.renderers.ExtendBrowsableAPIRenderer):
#         template = 'user/register/register.html'
#
#     renderer_classes = [CreateUserRenderer]
#
#     def get_queryset(self):
#         queryset = User.objects.none()
#         return queryset

class CreateUserView(views.APIView):
    """
    Creating user in browser only.
    """
    renderer_classes = [renderers.TemplateHTMLRenderer]
    template_name = 'user/register/register.html'
    queryset = User.objects.none()
    serializer_class = user.serializer.CreateUserSerializer
    # permission_classes = [restapi_app.permissions.IsNotAuthenticated]
    # throttle_classes = [throttling.AnonRateThrottle]

    def get_queryset(self):
        return User.objects.none()

    def get_success_headers(self, data):
        try:
            return {'Location': data[api_settings.URL_FIELD_NAME]}
        except (TypeError, KeyError):
            return {}

    def get(self, request):
        if request.user.is_authenticated():
            return Response({'data': 'Forbidden', 'status_code': status.HTTP_403_FORBIDDEN})

        unbound_user_instance = User()
        serializer = user.serializer.CreateUserSerializer(unbound_user_instance)
        headers = self.get_success_headers(serializer.data)
        response = Response(
            {'data': serializer.data, 'serializer': serializer, 'status_code': status.HTTP_200_OK}, headers=headers)
        return response

    def post(self, request, *args, **kwargs):
        """
        Create a model instance.
        """
        if request.user.is_authenticated():
            return Response({'data': 'Forbidden', 'status_code': status.HTTP_403_FORBIDDEN})
        return self.create(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):

        if User.objects.filter(username=request.data['username']).exists():
            message = 'User %s already exists' % request.data['username']
            return Response({'data': message, 'status_code': status.HTTP_409_CONFLICT})

        serializer = user.serializer.CreateUserSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def perform_create(self, serializer):
        serializer.save()




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
    USER PROFILE (restful instance allowing user to update details)
    Retrieve/Update/Destroy a user instance (must be authenticated and username=user)
    Users cannot change their username
    """
    serializer_class = user.serializer.UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'username'
    renderer_classes = [user.renderers.UserProfileBrowsableAPIRenderer, renderers.JSONRenderer]
    template_name = 'user/profile/profile.html'

    def get_queryset(self):
        """
        Return User info for currently authenticated user
        """
        user = self.request.user
        return User.objects.filter(username=user)




# class ChangePasswordView(views.APIView):
#     """
#     Changing password can only be done in browser
#     """
#     renderer_classes = [renderers.TemplateHTMLRenderer]
#     template_name = 'user/password/password_change.html'
#     queryset = User.objects.none()
#     serializer_class = user.serializer.UserPasswordChangeSerializer
#     throttle_classes = [throttling.AnonRateThrottle]
#
#     def get_success_headers(self, data):
#         try:
#             return {'Location': data[api_settings.URL_FIELD_NAME]}
#         except (TypeError, KeyError):
#             return {}
#
#     def get(self, request):
#         unbound_user_instance = User()
#         serializer = user.serializer.UserPasswordChangeSerializer(unbound_user_instance)
#         headers = self.get_success_headers(serializer.data)
#         response = Response(
#             {'data': serializer.data, 'serializer': serializer}, headers=headers, status=status.HTTP_200_OK)
#         return response
#
#     def patch(self, request):
#         # check username and email in request data (assign to data as request.data is immutable)
#         data = request.data.copy()
#         try:
#             username = data['username']
#             email = data['email']
#             password = data['password']
#         except KeyError:
#                 return Response(status=status.HTTP_404_NOT_FOUND)
#         except ValueError:
#                 return Response(status=status.HTTP_400_BAD_REQUEST)
#         try:
#             user_instance = User.objects.get(username=username)
#         except ValueError:
#             return Response({'detail': "No User"}, status=status.HTTP_400_BAD_REQUEST)
#
#         # Get associated user instance
#         if User.objects.filter(username=username).exists():
#             # user_instance = User.objects.filter(username=username, email=email)
#             user_instance = User.objects.get(username=username)
#             # Make sure the email submitted is the same as in db
#             # TODO THIS ISNT RETURNING USEFUL THINGS
#             print('user info')
#             print(user_instance.email, email)
#             print(user_instance.username, username)
#
#             if user_instance.email == email:
#                 # pop off the confirm_password field, raise exception if not equal
#                 confirm_password = data.pop('confirm_password')[0]
#
#                 if password != confirm_password:
#                     return Response({'detail': "Passwords do not match"}, status=status.HTTP_404_NOT_FOUND)
#
#                 print('match')
#                 # Only pass the new password to the serializer (no danger of overriding username/email combo)
#                 serializer = user.serializer.UserPasswordChangeSerializer(user_instance, data=data, partial=True)
#                 serializer.is_valid(raise_exception=True)
#
#                 if not serializer.is_valid():
#                     print('return not valid')
#                     # if not valid, return form bound with submitted data
#                     # return Response({'serializer': serializer, 'user': user})
#                     return Response({'detail': "Data format incorrect, please check your username and email inputs"},
#                                     status=status.HTTP_400_BAD_REQUEST)
#                 # Valid - go ahead and update
#                 self.perform_update(serializer)
#                 print(serializer)
#                 print('redirect...')
#                 return Response(serializer.data, template_name = 'user/password/password_change.html')
#                 # login_url = reverse('rest_framework:login')
#                 # return redirect(login_url)
#             else:
#                 raise restapi_app.exceptions.Conflict('Email %s is not associated with User %s' % (username, email))
#         else:
#             raise exceptions.NotFound(detail="Username not found")
#             # raise restapi_app.exceptions.CustomValidation("Username not found", 'detail', 404)
#
#     def perform_update(self, serializer):
#         serializer.save()

