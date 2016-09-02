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


class DataBrowserTests(APITestCase):
    """ This includes generic data-browser route tests that aren't specific
    to a particular level (e.g., formatting, content_negotiation, accepted routes) """

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
    URLS = [reverse('data_browser:root-list'),
            reverse('data_browser:survey-list', kwargs=_survey_kwargs),
            reverse("data_browser:astroobject-list", kwargs=_astroobject_kwargs),
            reverse("data_browser:trait-list", kwargs=_trait_kwargs),
            reverse("data_browser:subtraitproperty-list", kwargs=_trait_property_kwargs),
            reverse("data_browser:subtraitproperty-list", kwargs=_sub_trait_kwargs),
            reverse("data_browser:traitproperty-list", kwargs=_sub_trait_property_kwargs),
            ]

    def test_broken_links(self, urls=URLS):
        """ Ensure no broken links on Data Browser App. These may need updating as FIDIA is changed """
        for url in urls:
            _test_response = self.client.get(url)
            self.assertTrue(status.is_success(_test_response.status_code))

    def test_route_exists(self, urls=URLS):
        """ Check route exists. For these tests, this is identical to test_no_broken_links """
        for url in urls:
            self.client = APIClient()
            _test_response = self.client.get(url)
            self.assertTrue(status.is_success(_test_response.status_code))

    def test_route_options(self, urls=URLS):
        """ Test available route options (only in json as namespaced urls in the template cannot be parsed by the test APICLIENT for options... for some reason?)  """
        for url in urls:
            _test_options = self.client.options(path=url, content_type='application/json',
                                                HTTP_ACCEPT='application/json')

            self.assertTrue('renders' in _test_options.data)

            if url == '/asvo/data-browser/sami/24433/sfr_map/':
                self.assertEqual(_test_options.data['renders'], ['text/html', 'application/json', 'application/fits'])
            else:
                self.assertEqual(_test_options.data['renders'], ['text/html', 'application/json'])

            self.assertTrue('renders' in _test_options.data)
            self.assertEqual(_test_options.data['parses'],
                             ['application/json', 'application/x-www-form-urlencoded', 'multipart/form-data'])

    def test_unauthorized_endpoints(self, urls=URLS):
        """ Ensure delete/put/patch are not available """
        for url in urls:
            _test_post = self.client.post(data={'not_allowed'}, path=url, content_type='application/json',
                                          HTTP_ACCEPT='application/json')
            _test_put = self.client.put(data={'not_allowed'}, path=url, content_type='application/json',
                                        HTTP_ACCEPT='application/json')
            _test_patch = self.client.patch(data={'not_allowed'}, path=url, content_type='application/json',
                                            HTTP_ACCEPT='application/json')
            _test_delete = self.client.delete(data={'not_allowed'}, path=url, content_type='application/json',
                                              HTTP_ACCEPT='application/json')
            self.assertEqual(_test_post.data, {'detail': 'Method "POST" not allowed.'})
            self.assertEqual(_test_put.data, {'detail': 'Method "PUT" not allowed.'})
            self.assertEqual(_test_patch.data, {'detail': 'Method "PATCH" not allowed.'})
            self.assertEqual(_test_delete.data, {'detail': 'Method "DELETE" not allowed.'})

    def test_content_negotiation(self, urls=URLS):
        """ Vary the ACCEPT header (application/json, text/html) """
        for url in urls:
            _test_get = self.client.get(path=url, HTTP_ACCEPT='application/json')
            self.assertTrue(status.is_success(_test_get.status_code))
            self.assertEqual(_test_get.accepted_media_type, 'application/json')

            _test_get = self.client.get(path=url, HTTP_ACCEPT='text/html')
            self.assertTrue(status.is_success(_test_get.status_code))
            self.assertEqual(_test_get.accepted_media_type, 'text/html')

            _test_get = self.client.get(path=url, HTTP_ACCEPT='text/html')
            self.assertTrue(status.is_success(_test_get.status_code))
            self.assertEqual(_test_get.accepted_media_type, 'text/html')

    def test_content_type(self, urls=URLS):
        """ Content type == this is what I've got, will not affect ACCEPTED TYPES """
        for url in urls:
            _test_get = self.client.get(path=url, content_type='application/json', HTTP_ACCEPT='application/json')
            self.assertEqual(_test_get.accepted_media_type, 'application/json')
            _test_get = self.client.get(path=url, content_type='application/json', HTTP_ACCEPT='text/html')
            self.assertEqual(_test_get.accepted_media_type, 'text/html')
            _test_get = self.client.get(path=url, content_type='text/html', HTTP_ACCEPT='application/json')
            self.assertEqual(_test_get.accepted_media_type, 'application/json')
            _test_get = self.client.get(path=url, content_type='text/html', HTTP_ACCEPT='text/html')
            self.assertEqual(_test_get.accepted_media_type, 'text/html')

    def test_format(self, urls=URLS):
        """ Find available formats """
        for url in urls:
            _test_get = self.client.get(path=url, content_type='application/json', HTTP_ACCEPT='application/json',
                                        format='json')
            self.assertEqual(_test_get.accepted_media_type, 'application/json')

            # YOU MUST decode the byte string before trying to parse as JSON!!!
            self.assertTrue(is_json(_test_get.content.decode('utf-8')))

            # request with json format, but insist on accepting only html
            _test_get = self.client.get(path=url, content_type='text/html', HTTP_ACCEPT='text/html', format='json')
            self.assertFalse(is_json(_test_get.content.decode('utf-8')))

    def test_head(self, urls=URLS):
        """ The HEAD method is identical to GET except that the server MUST NOT return a
        message-body in the response """
        # _test_head = self.client.head(path=self.url)
        pass


class RootTests(APITestCase):
    """ Test route is available """
    url = reverse('data_browser:root-list')

    def test_response_data(self):
        """ Ensure response json is as expected """
        _test_response = self.client.get(self.url)
        self.assertIn('"surveys"', json.dumps(_test_response.data))
        _surveys = _test_response.data['surveys']
        self.assertEqual(len(_surveys), 2)
        self.assertTrue(is_json(json.dumps(_surveys)))

    def test_html_template(self):
        """ Test html template contains correct information """
        _test_response = self.client.get(self.url)
        self.assertTemplateUsed('data_browser/root/list.html')
        self.assertIn("What does the Data Browser do?", str(_test_response.content))

    def test_route_options_formats(self):
        """ Test specific route options for Root """
        _test_options = self.client.options(self.url)
        self.assertIn("Root List", json.dumps(_test_options.data))

    def test_renderer(self):
        """ Check the appropriate renderer is being used as per request config """
        _test_get = self.client.get(path=self.url, format='api', HTTP_ACCEPT='text/html')
        self.assertEqual(_test_get.accepted_renderer.__str__(), 'RootRenderer')

        _test_get = self.client.get(path=self.url, format='json', HTTP_ACCEPT='application/json')
        self.assertNotEqual(_test_get.accepted_renderer.__str__(), 'RootRenderer')

    def test_renderer_context(self):
        """ Ensure html context is available """
        _response = self.client.get(path=self.url)
        self.assertIn("What does the Data Browser do?", _response.content.decode('utf-8'))

    def test_caching(self):
        pass


class SurveyTests(APITestCase):
    """ Test route is available """

    url = reverse('data_browser:survey-list', kwargs=DataBrowserTests._survey_kwargs)

    def test_response_data(self):
        """ Ensure response json is as expected """
        _test_response = self.client.get(self.url)
        self.assertIn('"survey"', json.dumps(_test_response.data))
        self.assertIn('"astro_objects"', json.dumps(_test_response.data))
        self.assertEqual(_test_response.data['survey'], DataBrowserTests._survey_kwargs['sample_pk'])
        self.assertTrue(is_json(json.dumps(_test_response.data)))

    def test_html_template(self):
        """ Test html template contains correct information """
        _test_response = self.client.get(self.url)
        self.assertTemplateUsed('data_browser/survey/list.html')
        self.assertIn("Included?", str(_test_response.content))

    def test_route_options_formats(self):
        """ Test specific route options for Root """
        _test_options = self.client.options(self.url, HTTP_ACCEPT='application/json')
        self.assertIn("Survey List", json.dumps(_test_options.data))

    def test_renderer(self):
        """ Check the appropriate renderer is being used as per request config """
        _test_get = self.client.get(path=self.url, format='api', HTTP_ACCEPT='text/html')
        self.assertEqual(_test_get.accepted_renderer.__str__(), 'SurveyRenderer')

        _test_get = self.client.get(path=self.url, format='json', HTTP_ACCEPT='application/json')
        self.assertNotEqual(_test_get.accepted_renderer.__str__(), 'SurveyRenderer')

    def test_renderer_context(self):
        """ Ensure html context is available """
        _response = self.client.get(path=self.url)
        _str = "About "+DataBrowserTests._survey_kwargs['sample_pk'].upper()
        self.assertIn(_str, _response.content.decode('utf-8'))

    def test_caching(self):
        pass

# class SurveyTests(APITestCase):
#     """ Check each survey is available through FIDIA """
#
#     url = reverse('data_browser:survey-list', kwargs=DataBrowser._survey_kwargs),
#
#     def test_route_exists(self):
#         """ Check route exists. """
#         _test_response = self.client.get(self.url)
#         self.assertTrue(status.is_success(_test_response.status_code))
#
#     def test_response_data(self):
#         """ Ensure response json is as expected """
#         _test_response = self.client.get(self.url)
#         self.assertIn('"surveys"', json.dumps(_test_response.data))
#         _surveys = _test_response.data['surveys']
#         self.assertEqual(len(_surveys), 2)
#         self.assertTrue(is_json(json.dumps(_surveys)))
#
#     def test_html_template(self):
#         """ Test html template contains correct information """
#         _test_response = self.client.get(self.url)
#         self.assertTemplateUsed('data_browser/root/list.html')
#         self.assertIn("What does the Data Browser do?", str(_test_response.content))
#
#     def test_route_options_formats(self):
#         """ Test available route options and formats """
#         _test_options = self.client.options(self.url)
#         self.assertIn("Root List", json.dumps(_test_options.data))
#
#         self.assertTrue('renders' in _test_options.data)
#         self.assertEqual(_test_options.data['renders'], ['text/html', 'application/json'])
#
#         self.assertTrue('renders' in _test_options.data)
#         self.assertEqual(_test_options.data['parses'],
#                          ['application/json', 'application/x-www-form-urlencoded', 'multipart/form-data'])
#
#     def test_renderer(self):
#         """ Check the appropriate renderer is being used as per request config """
#         _test_get = self.client.get(path=self.url, format='api', HTTP_ACCEPT='text/html')
#         self.assertEqual(_test_get.accepted_renderer.__str__(), 'RootRenderer')
#
#         _test_get = self.client.get(path=self.url, format='json', HTTP_ACCEPT='application/json')
#         self.assertNotEqual(_test_get.accepted_renderer.__str__(), 'RootRenderer')
#
#     def test_unauthorized_endpoints(self):
#         """ Ensure delete/put/patch are not available """
#         _test_post = self.client.post(data={'not_allowed'}, path=self.url)
#         _test_put = self.client.put(data={'not_allowed'}, path=self.url)
#         _test_patch = self.client.patch(data={'not_allowed'}, path=self.url)
#         _test_delete = self.client.delete(data={'not_allowed'}, path=self.url)
#         self.assertEqual(_test_post.data, {'detail': 'Method "POST" not allowed.'})
#         self.assertEqual(_test_put.data, {'detail': 'Method "PUT" not allowed.'})
#         self.assertEqual(_test_patch.data, {'detail': 'Method "PATCH" not allowed.'})
#         self.assertEqual(_test_delete.data, {'detail': 'Method "DELETE" not allowed.'})
#
#     def test_content_negotiation(self):
#         """ Vary the ACCEPT header (application/json, text/html) """
#
#         _test_get = self.client.get(path=self.url, HTTP_ACCEPT='application/json')
#         self.assertTrue(status.is_success(_test_get.status_code))
#         self.assertEqual(_test_get.accepted_media_type, 'application/json')
#
#         _test_get = self.client.get(path=self.url, HTTP_ACCEPT='text/html')
#         self.assertTrue(status.is_success(_test_get.status_code))
#         self.assertEqual(_test_get.accepted_media_type, 'text/html')
#
#         _test_get = self.client.get(path=self.url, HTTP_ACCEPT='text/html')
#         self.assertTrue(status.is_success(_test_get.status_code))
#         self.assertEqual(_test_get.accepted_media_type, 'text/html')
#
#     def test_content_type(self):
#         """ Content type == this is what I've got, will not affect ACCEPTED TYPES """
#         _test_get = self.client.get(path=self.url, content_type='application/json', HTTP_ACCEPT='application/json')
#         self.assertEqual(_test_get.accepted_media_type, 'application/json')
#         _test_get = self.client.get(path=self.url, content_type='application/json', HTTP_ACCEPT='text/html')
#         self.assertEqual(_test_get.accepted_media_type, 'text/html')
#         _test_get = self.client.get(path=self.url, content_type='text/html', HTTP_ACCEPT='application/json')
#         self.assertEqual(_test_get.accepted_media_type, 'application/json')
#         _test_get = self.client.get(path=self.url, content_type='text/html', HTTP_ACCEPT='text/html')
#         self.assertEqual(_test_get.accepted_media_type, 'text/html')
#
#     def test_format(self):
#         """ Find available formats """
#         _test_get = self.client.get(path=self.url, content_type='application/json', HTTP_ACCEPT='application/json',
#                                     format='json')
#         self.assertEqual(_test_get.accepted_media_type, 'application/json')
#
#         # YOU MUST decode the byte string before trying to parse as JSON!!!
#         self.assertTrue(is_json(_test_get.content.decode('utf-8')))
#
#         # request with json format, but insist on accepting only html
#         _test_get = self.client.get(path=self.url, content_type='text/html', HTTP_ACCEPT='text/html', format='json')
#         self.assertFalse(is_json(_test_get.content.decode('utf-8')))
#
#     def test_head(self):
#         """ The HEAD method is identical to GET except that the server MUST NOT return a message-body in the response """
#         _test_head = self.client.head(path=self.url)
#         pass
#
#     def test_renderer_context(self):
#         """ Ensure html context is available """
#         _response = self.client.get(path=self.url)
#         self.assertIn("What does the Data Browser do?", _response.content.decode('utf-8'))
#
#     def test_caching(self):
#         pass
#
#     class GAMASample(object):
#         pass

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
