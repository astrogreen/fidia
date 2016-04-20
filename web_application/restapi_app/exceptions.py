from rest_framework.exceptions import APIException

class NoPropertyFound(APIException):
    status_code = 404
    default_detail = 'No Property found'