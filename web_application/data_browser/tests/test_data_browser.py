import json
from collections import Counter
from django.test import TestCase
from django.contrib.auth.models import User

from rest_framework.test import APIRequestFactory, APITestCase, APIClient, force_authenticate
from rest_framework import status, response
from rest_framework.reverse import reverse

from asvo.fidia_samples_archives import sami_dr1_sample, sami_dr1_archive as ar

import data_browser.views


#  python3 manage.py test data_browser.tests.test_data_browser


def is_json(myjson):
    try:
        json_object = json.loads(myjson)
    except ValueError:
        return False
    return True


class DataBrowser(APITestCase):

    def test_broken_links(self):
        """ Ensure no broken links on Data Browser App. These may need updating as FIDIA is changed """
        _survey_kwargs = {
            'sample_pk': 'sami',
        }
        _astroobject_kwargs = {
            'astroobject_pk': 24433,
            'sample_pk': 'sami',
        }
        _trait_kwargs = {
            'trait_pk': 'sfr_map',
            'astroobject_pk': 24433,
            'sample_pk': 'sami',
        }

        _trait_property_kwargs = {
            'subtraitproperty_pk': 'value',
            'trait_pk': 'sfr_map',
            'astroobject_pk': 24433,
            'sample_pk': 'sami',
        }
        _sub_trait_kwargs = {
            'subtraitproperty_pk': 'wcs',
            'trait_pk': 'line_map-NII6583',
            'astroobject_pk': 24433,
            'sample_pk': 'sami',
        }

        _sub_trait_property_kwargs = {
            'traitproperty_pk': '_wcs_string',
            'subtraitproperty_pk': 'wcs',
            'trait_pk': 'line_map-NII6583',
            'astroobject_pk': 24433,
            'sample_pk': 'sami',
        }

        _urls = [reverse('data_browser:root-list'),
                 reverse('data_browser:survey-list', kwargs=_survey_kwargs),
                 reverse("data_browser:astroobject-list", kwargs=_astroobject_kwargs),
                 reverse("data_browser:trait-list", kwargs=_trait_kwargs),
                 reverse("data_browser:subtraitproperty-list", kwargs=_trait_property_kwargs),
                 reverse("data_browser:subtraitproperty-list", kwargs=_sub_trait_kwargs),
                 reverse("data_browser:traitproperty-list", kwargs=_sub_trait_property_kwargs),
                 ]

        for u in _urls:
            _test_response = self.client.get(u)
            self.assertTrue(status.is_success(_test_response.status_code))


class Root(APITestCase):
    """ Test route is available """
    url = reverse('data_browser:root-list')

    def test_route_exists(self):
        """ Check route exists. """
        _test_response = self.client.get(self.url)
        self.assertTemplateUsed('data_browser/root/list.html')
        self.assertTrue(status.is_success(_test_response.status_code))
        self.assertIn("What does the Data Browser do?", str(_test_response.content))

    def test_response_data(self):
        _test_response = self.client.get(self.url)
        self.assertIn('"surveys"', json.dumps(_test_response.data))
        _surveys = _test_response.data['surveys']
        self.assertEqual(len(_surveys), 2)
        self.assertTrue(is_json(json.dumps(_surveys)))

    def test_html_template(self):
        """ Test html template contains correct information """
        pass

    def test_route_options_formats(self):
        """ Test available route options and formats """
        pass

    def test_route_authentication(self):
        """ Check unauthenticated users can access """
        pass

    def test_unauthorized_endpoints(self):
        """ Ensure delete/put/patch are not available """
        pass

    def test_content_negotiation(self):
        pass


class SurveyTests(APITestCase):
    """ Check each survey is available through FIDIA """

    class SAMISample(object):
        pass

    class GAMASample(object):
        pass

# class SampleTests(APITestCase):
#
#     url_list = reverse('sami-list')
#
#     class FIDIASample(object):
#         """
#         Returns: a python dict of AO in fidia sample or a str representing a json object from the python dict
#         """
#
#         current_sample = {}
#
#         for astro_object in sample:
#             url_kwargs = {
#                 'galaxy_pk': str(astro_object),
#             }
#             url = reverse("galaxy-list", kwargs=url_kwargs)
#             current_sample[str(astro_object)] = url
#
#         @classmethod
#         def dict(cls):
#             return cls.current_sample
#
#         @classmethod
#         def json_str(cls):
#             return json.dumps(cls.current_sample)
#
#     def setUp(self):
#         # Instantiate fidia sample to test against
#         self.fidia_sample = self.FIDIASample()
#         # Request Factor returns a request
#         self.factory = APIRequestFactory()
#         # Client returns a response (complete request-response cycle)
#         self.client = APIClient()
#         # Set up one user
#         self.user = User.objects.create_user(first_name='test_first_name', last_name='test_last_name',
#                                              username='test_user', email='test_user@test.com', password='test_password')
#         self.user.save()
#
#     def _require_login(self):
#         self.client.login(first_name='test_first_name', last_name='test_last_name',
#                           username='test_user', email='test_user@test.com', password='test_password')
#
#     # LIST
#     def test_list_resource_unauthenticated(self):
#         """HTTP_200_OK if unauthenticated"""
#         test_response = self.client.get(self.url_list)
#         self.assertTrue(status.is_success(test_response.status_code))
#         self.assertTemplateUsed(test_response, 'data_browser/sample/sample-list.html')
#         self.assertContains(test_response, text="sami/9352", status_code=200)
#
#         # JSON Format
#         # Before rendering
#         test_response_json = self.client.get(self.url_list+'?format=json')
#         self.assertEqual(test_response_json.data, self.fidia_sample.dict())
#
#         # After rendering
#         # Transform byte to str
#         decoded_response_content = test_response_json.content.decode('utf-8')
#         # parse str as json
#         # return dict object
#         parsed_json_to_dict = json.loads(decoded_response_content)
#         # return valid string representing json from a python obj (here, dict)
#         valid_json_string = json.dumps(parsed_json_to_dict)
#
#         self.assertEqual(valid_json_string, self.fidia_sample.json_str())
#
#     def test_create(self):
#         pass
#
#
# class AstroObjectTests(APITestCase):
#     pass
#
#
# class TraitTests(APITestCase):
#     pass
#
#
# class SubTraitTests(APITestCase):
#     pass
#
#
# class TraitPropertyTests(APITestCase):
#     pass
