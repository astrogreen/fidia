from django.utils.encoding import force_text

from rest_framework.exceptions import APIException
from rest_framework import status
from rest_framework.views import exception_handler


def custom_exception_handler(exc):
    """
    Custom exception handler for Django Rest Framework that adds
    the `status_code` to the response and renames the `detail` key to `error`.
    """
    response = exception_handler(exc)

    if response is not None:
        response.data['status_code'] = response.status_code
        response.data['error'] = response.data['detail']
        del response.data['detail']


class NoUserFound(APIException):
    status_code = status.HTTP_404_NOT_FOUND
    detail = 'No User found'


class UserAlreadyExists(APIException):
    status_code = status.HTTP_409_CONFLICT
    detail = 'User Already Exists'


class ServiceUnavailable(APIException):
    status_code = 503
    default_detail = 'Service temporarily unavailable, try again later.'



