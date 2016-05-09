from django.test import TestCase
from rest_framework.test import APIRequestFactory, APITestCase, APIClient, force_authenticate
from rest_framework import status, response
from rest_framework.reverse import reverse
from django.contrib.auth.models import User
from .views import QueryViewSet
from .models import Query

# factory = APIRequestFactory()
# data = {'title': 'my_test_SQL', 'SQL': 'SELECT * from InputCatA'}
# request = factory.post('/data/query/', data, format='json')
# request = factory.put('/data/query/1/', {'title': 'my_test_SQL', 'SQL': 'SELECT * from InputCatA'}, format='json')


class GeneralAPITests(APITestCase):
    def test_url_root(self):
        url = reverse('index')
        self.response = self.client.get(url)
        self.assertTrue(status.is_success(self.response.status_code))


class UserTests(APITestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.client = APIClient()
        self.user = User.objects.create_user(username='test_username', password='test_password')
        self.user.save()

    def test_create_account(self):
        """
        Ensure we can create a new User object
        """
        url = reverse('user-register')
        data = {'first_name': 'test_first_name', 'last_name': 'test_last_name', 'username': 'test_username_new',
                'email': 'test_username@test.com', 'password': 'test_password', 'confirm_password': "test_password"}
        self.response = self.client.post(url, data, format='json')
        self.assertEqual(self.response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.count(), 2)

    def test_create_account_already_exists(self):
        """
        Check response if user account already exists
        """
        url = reverse('user-register')
        data = {'first_name': 'test_first_name', 'last_name': 'test_last_name', 'username': 'test_username',
                'email': 'test_username@test.com', 'password': 'test_password', 'confirm_password': "test_password"}
        self.response = self.client.post(url, data, format='json')
        self.assertEqual(self.response.status_code, status.HTTP_409_CONFLICT)

    def test_create_account_mismatch_passwords(self):
        """
        Check response if user enters mis-matched passwords
        """
        pass

    def test_create_account_incomplete_data(self):
        """
        Check response if user doesn't fill out all fields
        """
        pass

class QueryTests(APITestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.client = APIClient()
        self.user = User.objects.create_user('test_user', email='test_user@test.com', password='test_password')
        self.user.save()

    def _require_login(self):
        self.client.login(username='test_user', password='test_password')

    # list of resources
    def test_list_url(self):
        """
        list view is forbidden (403) if unauthenticated, HTTP_200_OK if authenticated

        """
        #TODO this should be 401 UNAUTHORIZED
        url = reverse('query-list')
        self.response = self.client.get(url)
        # status.is_success / status.is_client_error helper functions from DRF
        # can test for range (e.g., successful == 2xx)
        self.assertTrue(status.is_client_error(self.response.status_code))

    def test_list_url_authenticated(self):
        """
        list view HTTP_200_OK if authenticated

        """
        self._require_login()
        url = reverse('query-list')
        self.response = self.client.get(url)
        self.assertTrue(status.is_success(self.response.status_code))

    def test_list_resource_unauthenticated(self):
        pass

    def test_list_resource_authenticated(self):
        pass

    # single resource endpoint
    def test_create_new_resource(self):
        pass

    def test_retrieve_resource(self):
        pass

    def test_retrieve_resource_header(self):
        pass

    def test_retrieve_resource_options(self):
        pass

    def test_put_resource(self):
        pass

    def test_patch_resource(self):
        pass

    def test_delete_resource(self):
        pass
