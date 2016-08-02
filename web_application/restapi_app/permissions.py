from rest_framework import permissions


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object to edit it
    """
    def has_object_permission(self, request, view, obj):
        #read permissions are allowed to any request,
        #so we'll always allow GET, HEAD or OPTIONS requests
        if request.method in permissions.SAFE_METHODS:
            return True

        #write permissions are only allowed to owner of snippet
        return obj.owner == request.user
        #returns true false


SAFE_METHODS = ['POST']


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