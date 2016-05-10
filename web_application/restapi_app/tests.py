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
spark_on = True

class GeneralAPITests(APITestCase):
    def test_url_root(self):
        url = reverse('index')
        self.response = self.client.get(url)
        self.assertTrue(status.is_success(self.response.status_code))


class UserTests(APITestCase):
    url = reverse('user-register')

    def setUp(self):
        self.factory = APIRequestFactory()
        self.client = APIClient()
        self.user = User.objects.create_user(username='test_username', password='test_password')
        self.user.save()

    def test_create_account(self):
        """
        Ensure we can create a new User object
        """
        data = {'first_name': 'test_first_name', 'last_name': 'test_last_name', 'username': 'test_username_new',
                'email': 'test_username@test.com', 'password': 'test_password', 'confirm_password': "test_password"}
        self.response = self.client.post(self.url, data, format='json')
        self.assertEqual(self.response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.count(), 2)
        # self.assertEqual(test_response.data, {'id': 1, 'title': 'test_title'})

    def test_create_account_already_exists(self):
        """
        Check response if user account already exists
        """
        data = {'first_name': 'test_first_name', 'last_name': 'test_last_name', 'username': 'test_username',
                'email': 'test_username@test.com', 'password': 'test_password', 'confirm_password': "test_password"}
        self.response = self.client.post(self.url, data, format='json')
        self.assertEqual(self.response.status_code, status.HTTP_409_CONFLICT)

    def test_create_account_mismatch_passwords(self):
        """
        Check response if user enters mis-matched passwords
        """
        data = {'first_name': 'test_first_name', 'last_name': 'test_last_name', 'username': 'test_username_new',
                'email': 'test_username@test.com', 'password': 'test_password',
                'confirm_password': "test_password_incorrect"}
        self.response = self.client.post(self.url, data, format='json')
        self.assertEqual(self.response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_account_incomplete_data(self):
        """
        Check response if user doesn't fill out all fields
        """
        data = {'username': 'test_username_new2', 'password': 'test_password',
                'confirm_password': "test_password"}
        self.response = self.client.post(self.url, data, format='json')
        self.assertEqual(self.response.status_code, status.HTTP_400_BAD_REQUEST)


class QueryTests(APITestCase):
    url = reverse('query-list')

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

    # List of resources
    def test_list_resource_unauthenticated(self):
        """List view is forbidden (403) if unauthenticated, HTTP_200_OK if authenticated"""
        # TODO this should be 401 UNAUTHORIZED
        url = reverse('query-list')
        test_response = self.client.get(url)
        self.assertTrue(status.is_client_error(test_response.status_code))

    def test_list_resource_authenticated(self):
        """List view HTTP_200_OK if authenticated"""
        self._require_login()
        url = reverse('query-list')
        test_response = self.client.get(url)
        self.assertTrue(status.is_success(test_response.status_code))

    # Single resource endpoint
    def test_create_new_resource_unauthenticated(self):
        """Create resource without authentication"""
        self.client.logout()
        data = {
            "title": "test_title",
            "SQL": "SELECT * FROM SAMI LIMIT 10",
            "queryResults": "null",
        }
        test_response = self.client.post(self.url, data, format='json')
        self.assertTrue(status.is_client_error(test_response.status_code))
        self.assertEqual(Query.objects.count(), 0)

    def test_create_new_resource_authenticated(self):
        """Create resource with authentication"""
        self._require_login()
        data = {
            "title": "test_title",
            "SQL": "SELECT t1.sami_id, t1.cube_available FROM SAMI AS t1 LIMIT 1",
        }
        test_response = self.client.post(self.url, data, format='json')
        self.assertEqual(test_response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Query.objects.count(), 1)

    def test_create_new_resource_incorrect_data(self):
        """ Create a new resource if logged in and data correct """
        self._require_login()
        data = {
            "title": "test_title"
        }
        test_response = self.client.post(self.url, data, format='json')
        self.assertTrue(status.is_client_error(test_response.status_code))
        # Assert new resource does not exist
        self.assertEqual(Query.objects.count(), 0)
        data = {
            "title": "test_title",
            "SQL": "",
        }
        test_response_2 = self.client.post(self.url, data, format='json')
        self.assertTrue(status.is_client_error(test_response_2.status_code))
        # Assert new resource does not exist
        self.assertEqual(Query.objects.count(), 0)

    def test_retrieve_resource(self):
        """Retrieve Query Data"""
        pass
        # self._require_login()
        # Create Query
        # url = self.url+'1/'
        #
        # self.response = self.client.get(url)
        # self.assertTrue(status.is_success(self.response.status_code))

    def test_retrieve_resource_unauthenticated(self):
        """Retrieve query data if unauthenticated"""
        self.client.logout()
        url = self.url + '1/'
        self.response = self.client.get(url)
        self.assertTrue(status.is_client_error(self.response.status_code))

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
