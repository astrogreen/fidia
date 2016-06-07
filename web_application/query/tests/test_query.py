import json
from django.test import TestCase
from django.contrib.auth.models import User

from rest_framework.test import APIRequestFactory, APITestCase, APIClient, force_authenticate
from rest_framework import status, response
from rest_framework.reverse import reverse

from query.models import Query

# factory = APIRequestFactory()
# data = {'title': 'my_test_SQL', 'SQL': 'SELECT * from InputCatA'}
# request = factory.post('/data/query/', data, format='json')
# request = factory.put('/data/query/1/', {'title': 'my_test_SQL', 'SQL': 'SELECT * from InputCatA'}, format='json')

# python3 manage.py test query.tests.test_query

spark_on = True


def is_json(myjson):
    try:
        json_object = json.loads(myjson)
    except ValueError:
        return False
    return True

class QueryTests(APITestCase):
    url_list = reverse('query-list')
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

    def test_list_resource_authenticated(self):
        """List view HTTP_200_OK if authenticated"""
        self._require_login()
        test_response = self.client.get(self.url_list)
        self.assertTrue(status.is_success(test_response.status_code))

    def test_list_authenticated_incorrect_method(self):
        """Make a POST request at the query-list view"""
        self._require_login()
        data = {'title': "test_title", "SQL": "SELECT * FROM SAMI LIMIT 1"}
        test_response = self.client.post(self.url_list, data, format='json')
        self.assertEqual(test_response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertEqual(Query.objects.count(), 0)

    # CREATE
    #  -- Authenticated
    def test_create_new_resource_authenticated(self):
        """Create resource with authentication"""
        self._require_login()
        data = {
            "title": "test_title",
            "SQL": "SELECT * FROM SAMI LIMIT 1",
        }
        test_response = self.client.post(self.url_create, data, format='json')
        self.assertEqual(test_response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Query.objects.count(), 1)

    def test_create_new_resource_authenticated_check_queryresults(self):
        """Create resource with authentication and query results, which should be overridden
            Note, the results aren't passed back to response.content, but a url is... check for that.
        """
        self._require_login()
        data = {
            "title": "test_title",
            "SQL": "SELECT * FROM SAMI LIMIT 1",
            "queryResults": "null",
        }
        test_response = self.client.post(self.url_create, data, format='json')
        self.assertEqual(test_response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Query.objects.count(), 1)
        resource_url = "http://testserver/asvo/query-history/1/"
        # print(test_response.content.decode())
        self.assertContains(test_response, text=resource_url, status_code=201)
        self.assertTemplateUsed(test_response, 'query/query-create.html')

    def test_create_new_resource_authenticated_malformed(self):
        """Create resource with authentication and malformed json"""
        self._require_login()
        data = {'title': "test_title", "surprisefield": "SELECT * FROM SAMI LIMIT 1"}
        test_response = self.client.post(self.url_create, data, format='json')
        self.assertEqual(test_response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Query.objects.count(), 0)
        self.assertTemplateUsed(test_response, 'query/query-create.html')

    def test_create_new_resource_authenticated_SQL_empty(self):
        """Create resource with authentication and malformed json"""
        self._require_login()
        data = {'title': "test_title", "surprisefield": "SELECT * FROM SAMI LIMIT 1"}
        test_response = self.client.post(self.url_create, data, format='json')
        print(test_response.data)
        self.assertEqual(test_response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Query.objects.count(), 0)
        self.assertEqual(test_response.data, {'detail': 'Incomplete request - SQL field missing'})
        # Check user can see this
        self.assertContains(test_response, text="Incomplete request - SQL field missing", status_code=400)

    #  -- Unauthenticated
    def test_create_new_resource_unauthenticated(self):
        """Create resource without authentication"""
        self.client.logout()
        data = {
            "title": "test_title",
            "SQL": "SELECT * FROM SAMI LIMIT 10",
            "queryResults": "null",
        }
        test_response = self.client.post(self.url_create, data, format='json')
        self.assertTrue(status.is_client_error(test_response.status_code))
        self.assertEqual(Query.objects.count(), 0)

    def test_retrieve_resource_authenticated(self):
        """ Create & Retrieve Query Data"""
        self._require_login()
        data = {
            "title": "test_title",
            "SQL": "SELECT t1.sami_id, t1.cube_available FROM SAMI AS t1 LIMIT 1",
        }
        test_response_create_resource = self.client.post(self.url_create, data, format='json')
        self.assertEqual(test_response_create_resource.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Query.objects.count(), 1)
        test_url = 'http://testserver/asvo/query-history/1/'
        test_response_retrieve = self.client.get(test_url)
        self.assertEqual(test_response_retrieve.data['title'], "test_title")
        self.assertEqual(test_response_retrieve.data['owner'], 'test_user')

        # Test Request Media Types
        test_response_retrieve_json = self.client.get(test_url, format='json')
        # self.assertEqual(json.loads(response.content), {'id': 4, 'username': 'lauren'})

        # print(test_response_retrieve_json.data)
        # print(str(test_response_retrieve_json.content))
        # print(is_json(test_response_retrieve_json.content))

        # self.assertTrue(is_json(test_response_retrieve.data))
        # self.assertContains(json.loads(test_response_retrieve.data), 'json')

        # test_request_csv = self.factory.get(test_url, format="csv")
        # self.assertEqual(test_request_csv)
        # print(test_request.accepted_renderer)
        # print(test_request.accepted_media_type)

    def test_retrieve_resource_unauthenticated(self):
        """Retrieve query data if unauthenticated: nope"""
        self.client.logout()
        url = self.url_list + '1/'
        url = 'http://testserver/asvo/query-history/1/'
        self.response = self.client.get(url)
        self.assertTrue(status.is_client_error(self.response.status_code))



    def test_retrieve_resource_header(self):
        pass

    def test_retrieve_resource_options(self):
        pass

    def test_patch_results_illegal(self):
        pass

    def test_put_resource(self):
        pass

    def test_patch_resource(self):
        pass

    def test_delete_resource(self):
        pass
