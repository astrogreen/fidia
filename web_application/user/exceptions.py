from django.utils.encoding import force_text

from rest_framework.exceptions import APIException
from rest_framework import status


class NoUserFound(APIException):
    status_code = status.HTTP_404_NOT_FOUND
    detail = 'No User found'
