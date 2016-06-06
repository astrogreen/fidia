from rest_framework.exceptions import APIException

class BadSQL(APIException):
    status_code = 400
    default_detail = 'Bad Request'
