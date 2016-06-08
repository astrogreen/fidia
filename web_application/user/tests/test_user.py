import json
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


class UserTests(APITestCase):

    url_create = reverse('user-register')

    def setUp(self):
        # Request Factor returns a request
        self.factory = APIRequestFactory()
        # Client returns a response (complete request-response cycle)
        self.client = APIClient()
        # Set up one user
        self.user = User.objects.create_user(first_name='test_first_name', last_name='test_last_name',
                                             username='test_user', email='test_user@test.com', password='test_password')
        self.user.save()
        self.url_detail = reverse('user-profile-detail', kwargs={'username': 'test_user'})

        self.user_dict = {
            'first_name': "another user",
            'last_name': "test",
            'email': "test@hotmail.com",
            'username': "test_user_2",
            'password': 'test',
            'confirm_password': 'test',
        }

    def _require_login(self):
        self.client.login(first_name='test_first_name', last_name='test_last_name',
                          username='test_user', email='test_user@test.com', password='test_password')

    # CREATE
    def test_create_resource_unauthenticated(self):
        """
        unauthenticated users should be able to create a user
        """
        test_response = self.client.post(self.url_create, self.user_dict, format='json')
        self.assertTrue(status.is_success(test_response.status_code))

    def test_create_resource_authenticated(self):
        self._require_login()
        test_response = self.client.post(self.url_create, self.user_dict, format='json')
        self.assertTrue(status.is_client_error(test_response.status_code))

    def test_retrieve_resource_unauthenticated(self):
        """
        Unauthenticated users shouldn't see username's details
        """
        test_response = self.client.get(self.url_detail)
        self.assertEqual(test_response.status_code, 403)
        self.assertTrue(status.is_client_error(test_response.status_code))

    def test_retrieve_resource_authenticated(self):
        """
        Unauthenticated users shouldn't see username's details
        """
        self._require_login()
        test_response = self.client.get(self.url_detail)
        self.assertEqual(test_response.data,
                         {'first_name': 'test_first_name', 'username': 'test_user', 'last_name': 'test_last_name',
                          'email': 'test_user@test.com'})
        self.assertTrue(status.is_success(test_response.status_code))

    def test_login_unauthenticated(self):
        login_url = reverse('rest_framework:login')
        test_response = self.client.get(login_url)
        self.assertTrue(status.is_success(test_response.status_code))


    def test_login_redirect(self):
        self._require_login()
        login_url = reverse('rest_framework:login')
        test_response = self.client.get(login_url)
        print(vars(test_response))
        # self.assertTrue(status.is_success(test_response.status_code))

        pass

# class AdminUserTests(APITestCase):
#     url_list = reverse('user-list')
#     url_detail = reverse('user-detail')
#     pass
