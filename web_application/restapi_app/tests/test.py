from django.test import TestCase
from rest_framework.test import APIRequestFactory, APITestCase, APIClient, force_authenticate
from rest_framework import status, response
from rest_framework.reverse import reverse


# response.data = unrendered response (still python dict)
# response.content = rendered response

class GeneralAPITests(APITestCase):
    def test_url_root(self):
        url = reverse('index')
        self.response = self.client.get(url)
        self.assertTrue(status.is_success(self.response.status_code))

    def test_if_url_does_not_exist(self):
        pass