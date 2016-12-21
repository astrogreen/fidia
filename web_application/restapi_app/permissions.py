from django.http import Http404
from django.contrib.auth.models import Group, User
from rest_framework import permissions


# class IsOwnerOrReadOnly(permissions.BasePermission):
#     """
#     Custom permission to only allow owners of an object to edit it
#     """
#     SAFE_METHODS = ['POST']
#
#     def has_object_permission(self, request, view, obj):
#         # read permissions are allowed to any request,
#         # so we'll always allow GET, HEAD or OPTIONS requests
#         if request.method in permissions.SAFE_METHODS:
#             return True
#
#         # write permissions are only allowed to owner of snippet
#         return obj.owner == request.user
#         # returns true false


class IsNotAuthenticated(permissions.BasePermission):
    """
    Custom permission to only allow only unauthenticated users (registration page)
    """

    def has_object_permission(self, request, view, obj):
        return False

    def has_permission(self, request, view):
        # return false if user is authenticated and get request (allow authentication in post)
        # value = not (request.user and request.user.is_authenticated())
        # if request.method == 'POST':
        #     value = True
        # return value
        return not (request.user and request.user.is_authenticated())


class IsAdminOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):

        return (
            request.method in permissions.SAFE_METHODS or
            request.user and
            request.user.is_staff
        )


class IsSurveyTeamOrAdminElseReadOnly(permissions.DjangoObjectPermissions):
    """ Admin accesses all actions, if user group matches object 'edit_group' field,
        then grant temporary access to the update action on this object. """

    def has_permission(self, request, view):

        return (request.method in permissions.SAFE_METHODS or
                request.user and request.user.is_staff
                )

    def has_object_permission(self, request, view, obj):
        print('IsSurveyTeamOrAdminElseReadOnly: OBJECT')
        _is_survey_team = False

        for g in request.user.groups.all():
            if hasattr(obj, 'edit_group'):
                if hasattr(obj.edit_group, 'name'):
                    if obj.edit_group.name == g.name:
                        _is_survey_team = True
        print(
            request.method in permissions.SAFE_METHODS or
            request.user and request.user.is_staff or
            request.user and _is_survey_team and request.method == 'PUT'
        )
        return (
            request.method in permissions.SAFE_METHODS or
            request.user and request.user.is_staff or
            request.user and _is_survey_team and request.method == 'PUT'
        )

