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
import user.renderers


class CreateUserView(generics.ListCreateAPIView):
    """
    User View to allow registration
    Throttle by IP to twice a day?
    """
    model = User
    permission_classes = [restapi_app.permissions.IsNotAuthenticated]
    serializer_class = user.serializer.CreateUserSerializer
    throttle_classes = [throttling.AnonRateThrottle]

    class CreateUserRenderer(restapi_app.renderers.ExtendBrowsableAPIRenderer):
        template = 'user/register/register.html'

    renderer_classes = [CreateUserRenderer]

    def get_queryset(self):
        queryset = User.objects.none()
        return queryset
    #
    # def perform_create(self, serializer):
    #     """
    #     Redirect if browsable api to logged-in view of profile
    #     """
    #     serializer.save()
    #     # LOGIN if browsable API
    #     if self.request.accepted_media_type == 'text/html':
    #         new_user = authenticate(username=serializer.validated_data['username'], password=serializer.validated_data['password'])
    #         if user is not None:
    #             login(self.request, new_user)
    #             redirect_url = reverse('user-profile-detail', kwargs=({'username': serializer.validated_data['username']}))
    #             return HttpResponseRedirect(redirect_url)


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

    def get_queryset(self):
        """
        Return User info for currently authenticated user
        """
        user = self.request.user
        return User.objects.filter(username=user)


class UserViewSet(viewsets.ReadOnlyModelViewSet):
    """
    If Admin, view all users at this route
    If not, view only user detail
    """
    queryset = User.objects.all()
    serializer_class = user.serializer.UserSerializer
    permission_classes = [permissions.IsAdminUser]



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

