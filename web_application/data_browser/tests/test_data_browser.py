import json
from django.test import TestCase
from django.contrib.auth.models import User

from rest_framework.test import APIRequestFactory, APITestCase, APIClient, force_authenticate
from rest_framework import status, response
from rest_framework.reverse import reverse

import data_browser.views

from fidia.archive.sami import SAMITeamArchive
from django.conf import settings
ar = SAMITeamArchive(
    settings.SAMI_TEAM_DATABASE,
    settings.SAMI_TEAM_DATABASE_CATALOG)

sample = ar.get_full_sample()

#  python3 manage.py test data_browser.tests.test_data_browser


def is_json(myjson):
    try:
        json_object = json.loads(myjson)
    except ValueError:
        return False
    return True


class SampleTests(APITestCase):

    url_list = reverse('sami-list')

    class FIDIASample(object):
        """
        Returns: a python dict of AO in fidia sample or a str representing a json object from the python dict
        """

        current_sample = {}

        for astro_object in sample:
            url_kwargs = {
                'galaxy_pk': str(astro_object),
            }
            url = reverse("galaxy-list", kwargs=url_kwargs)
            current_sample[str(astro_object)] = url

        @classmethod
        def dict(cls):
            return cls.current_sample

        @classmethod
        def json_str(cls):
            return json.dumps(cls.current_sample)

    def setUp(self):
        # Instantiate fidia sample to test against
        self.fidia_sample = self.FIDIASample()
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
        """HTTP_200_OK if unauthenticated"""
        test_response = self.client.get(self.url_list)
        self.assertTrue(status.is_success(test_response.status_code))
        self.assertTemplateUsed(test_response, 'data_browser/sample/sample-list.html')
        self.assertContains(test_response, text="sami/9352", status_code=200)

        # JSON Format
        # Before rendering
        test_response_json = self.client.get(self.url_list+'?format=json')
        self.assertEqual(test_response_json.data, self.fidia_sample.dict())

        # After rendering
        # Transform byte to str
        decoded_response_content = test_response_json.content.decode('utf-8')
        # parse str as json
        # return dict object
        parsed_json_to_dict = json.loads(decoded_response_content)
        # return valid string representing json from a python obj (here, dict)
        valid_json_string = json.dumps(parsed_json_to_dict)

        self.assertEqual(valid_json_string, self.fidia_sample.json_str())

    def test_create(self):
        pass


class AstroObjectTests(APITestCase):
    pass


class TraitTests(APITestCase):
    pass


class SubTraitTests(APITestCase):
    pass


class TraitPropertyTests(APITestCase):
    pass
