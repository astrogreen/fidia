from rest_framework.test import APIRequestFactory, APITestCase, APIClient, force_authenticate
from rest_framework import status, response
from rest_framework.reverse import reverse
from django.contrib.auth.models import User
from restapi_app.models import Query
from restapi_app.views import QueryViewSet
import json


def is_json(myjson):
    print(myjson)
    try:
        json_object = json.loads(myjson)
    except ValueError:
        return False
    return True


class RendererTests(APITestCase):
    url = reverse('query-list')
    data = {
        "title": "test_title",
        "SQL": "SELECT t1.sami_id, t1.cube_available FROM SAMI AS t1 LIMIT 1",
    }
    spark_on = False

    def setUp(self):
        # Client returns a response (complete request-response cycle)
        self.client = APIClient()
        # Request Factor returns a request
        self.factory = APIRequestFactory()

        # Set up one user
        self.user = User.objects.create_user(first_name='test_first_name', last_name='test_last_name',
                                             username='test_user', email='test_user@test.com', password='test_password')
        self.user.save()

        # # Create a request with data to create Query object
        # test_request = self.factory.post(self.url, data=self.data)
        #
        # # Forcibly authenticate the request
        # force_authenticate(test_request, user=self.user)

        # Create a new Query Object using the request
        # instance = Query.objects.create(title="test_query", SQL="SELECT * FROM SAMI LIMIT 1", owner=self.user)
        self.query = Query.objects.create(title="test_query", SQL="SELECT * FROM SAMI LIMIT 1", owner=self.user,
                                          queryResults={'index': [0], 'data': [[0, '6821', False]], 'columns': ['index', 'sami_id', 'cube_available']})
        self.query.save()

        # Get URL of new resource
        self.resource_url = reverse('query-detail', kwargs={'pk': self.query.id})
        self.assertEqual(Query.objects.count(), 1)

    def _require_login(self):
        self.client.login(first_name='test_first_name', last_name='test_last_name',
                          username='test_user', email='test_user@test.com', password='test_password')

    def test_json_renderer_dummy_data(self):
        """
        Retrieve Query Data - format JSON. This is dummy data to improve testing speeds.
        Responses from DRF aren't yet rendered as template response rendering is performed by django's
         internal request-response cycle. We need to first render the response, then inspect response.content
        """
        self.assertEqual(Query.objects.count(), 1)
        # Specify the view and mapping request type to CRUD action
        view = QueryViewSet.as_view({'get': 'retrieve'})
        # Create a test request
        test_request_retrieve = self.factory.get(self.resource_url, format="json")
        # Forcibly authenticate the request
        force_authenticate(test_request_retrieve, user=self.user)

        test_response_retrieve = view(test_request_retrieve, pk='1', format="json")
        # Render the HTML/json/csv for the chosen representation.
        test_response_retrieve.render()

        print(type(test_response_retrieve.content))
        print(json.loads(test_response_retrieve.content))
        # print(is_json(str(test_response_retrieve.content)))
        #
        # test_response_retrieve_json = self.client.get(self.resource_url, content_type='application/json')
        #
        # print(test_response_retrieve_json.data)
        # print(test_response_retrieve_json.accepted_renderer)
        # # render() method needs to be called before inspect .content
        # print(test_response_retrieve_json.accepted_media_type)
        #
        # # print(is_json(test_response_retrieve_json.data))


    def test_json_renderer_real_data(self):
        """
        Note here we create the Query Object through the view as the .create method
        is custom (calls fidia) and we need to test the throughput of truncated_api_response_data()
        This is slower than the dummy Query object instance above
        """
        if self.spark_on:
            self._require_login()
            new_query = self.client.post(self.url, self.data, format='json')
            resource_url = new_query.data['url']
            self.assertEqual(new_query.status_code, status.HTTP_201_CREATED)
            self.assertEqual(Query.objects.count(), 2)
            new_query_retrieve = self.client.get(resource_url)

            print(resource_url)
            print(new_query_retrieve.data['queryResults'])
        else:
            pass
    # def test_csv_renderer(self):
    #     """ Create & Retrieve Query Data - format csv """
    #     self._require_login()
    #     data = {
    #         "title": "test_title",
    #         "SQL": "SELECT t1.sami_id, t1.cube_available FROM SAMI AS t1 LIMIT 1",
    #     }
    #     test_response_create_resource = self.client.post(self.url, data, format='json')
    #     self.assertEqual(test_response_create_resource.status_code, status.HTTP_201_CREATED)
    #     self.assertEqual(Query.objects.count(), 1)
    #     test_url = self.url+'1/'
    #     test_response_retrieve = self.client.get(test_url)
    #     self.assertEqual(test_response_retrieve.data['title'], "test_title")
    #     self.assertEqual(test_response_retrieve.data['owner'], 'test_user')
    #
    #     # Test Request Media Types
    #     test_response_retrieve_csv = self.client.get(test_url, format='csv')
    #     print(test_response_retrieve_csv.data)
    #     # self.assertEqual(json.loads(response.content), {'id': 4, 'username': 'lauren'})
    #
    #     # print(test_response_retrieve_json.data)
    #     # print(str(test_response_retrieve_json.content))
    #     # print(is_json(test_response_retrieve_json.content))
    #
    #     # self.assertTrue(is_json(test_response_retrieve.data))
    #     # self.assertContains(json.loads(test_response_retrieve.data), 'json')
    #
    #     # test_request_csv = self.factory.get(test_url, format="csv")
    #     # self.assertEqual(test_request_csv)
    #     # print(test_request.accepted_renderer)
    #     # print(test_request.accepted_media_type)
    #
