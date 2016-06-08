import json
from django.test import TestCase
from django.contrib.auth.models import User

from rest_framework.test import APIRequestFactory, APITestCase, APIClient, force_authenticate
from rest_framework import status, response
from rest_framework.reverse import reverse

# factory = APIRequestFactory()
# data = {'title': 'my_test_SQL', 'SQL': 'SELECT * from InputCatA'}
# request = factory.post('/data/query/', data, format='json')
# request = factory.put('/data/query/1/', {'title': 'my_test_SQL', 'SQL': 'SELECT * from InputCatA'}, format='json')

# python3 manage.py test uesr.tests.test_user

spark_on = True


def is_json(myjson):
    try:
        json_object = json.loads(myjson)
    except ValueError:
        return False
    return True


class AdminUserTests(APITestCase):
    url_list = reverse('user-list')
    url_detail = reverse('user-detail')
    pass


class UserTests(APITestCase):
    url_list = reverse('user-list')
    url_create = reverse('query-create-list')

    def setUp(self):
        # Request Factor returns a request
        self.factory = APIRequestFactory()
        # Client returns a response (complete request-response cycle)
        self.client = APIClient()
        # Set up one user
        self.user = User.objects.create_user(first_name='test_first_name', last_name='test_last_name',
                                             username='test_user', email='test_user@test.com', password='test_password')
        self.user.save()

    def _require_login(self):
        self.client.login(first_name='test_first_name', last_name='test_last_name',
                          username='test_user', email='test_user@test.com', password='test_password')

    # LIST
    def test_list_resource_unauthenticated(self):
        """List view is forbidden (403) if unauthenticated, HTTP_200_OK if authenticated"""
        # TODO this should be 401 UNAUTHORIZED
        test_response = self.client.get(self.url_list)
        self.assertTrue(status.is_client_error(test_response.status_code))