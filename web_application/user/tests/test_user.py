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

# response.content.decode("utf-8")
# turn response.content into a UTF-8 encoded string before passing it to self.assertJSONEqual
# json.dumps Serialize ``obj`` to a JSON formatted ``str``.
# json.loads Deserialize ``s`` (a ``str`` instance containing a JSON document) to a Python object.


def is_json(myjson):
    try:
        json_object = json.loads(myjson)
    except ValueError:
        return False
    return True


class TestSetUp(APITestCase):
    """ Mixin to add setup functionality """
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


class UserRegistrationTests(TestSetUp, APITestCase):

    url_create = reverse('user-register')

    # CREATE (REGISTER)
    def test_create_resource_check_template(self):
        """ Check template used at /register/ """
        test_response = self.client.get(self.url_create)
        self.assertTrue(status.is_success(test_response.status_code))
        self.assertTemplateUsed('user/register/register.html')

    def test_create_resource_unauthenticated(self):
        """ Unauthenticated users should be able to create a user """
        test_response = self.client.post(self.url_create, self.user_dict, format='json')
        self.assertTrue(status.is_success(test_response.status_code))

    def test_create_resource_authenticated(self):
        """ Unauthenticated users shouldn't be able to register """
        self._require_login()
        test_response = self.client.post(self.url_create, self.user_dict, format='json')
        self.assertTrue(status.is_client_error(test_response.status_code))

    def test_create_resource_username_too_long(self):
        pass

    def test_create_resource_username_exists(self):
        pass


class UserProfileTests(TestSetUp, APITestCase):
    url_detail = reverse('user-profile-detail', kwargs={'username': 'test_user'})

    # RETRIEVE (ACCOUNTS/USERNAME)
    def test_retrieve_resource_check_template(self):
        """ Check template used at /accounts/ """
        self._require_login()
        test_response = self.client.get(self.url_detail)
        self.assertTrue(status.is_success(test_response.status_code))
        self.assertTemplateUsed('user/profile/profile.html')

    def test_retrieve_resource_unauthenticated(self):
        """ Unauthenticated users shouldn't see username's details
        /accounts/username/
        """
        test_response = self.client.get(self.url_detail)
        self.assertEqual(test_response.status_code, 403)
        self.assertTrue(status.is_client_error(test_response.status_code))

    def test_retrieve_resource_authenticated(self):
        """
        Authenticated users get profile details
        /accounts/username/
        """
        self._require_login()
        test_response = self.client.get(self.url_detail)
        self.assertEqual(test_response.data,
                         {'last_name': 'test_last_name', 'username': 'test_user', 'first_name': 'test_first_name',
                          'query': [], 'email': 'test_user@test.com'})
        self.assertTrue(status.is_success(test_response.status_code))

    def test_retrieve_resource_incorrect_method(self):
        """Authenticated user post to /accounts/username"""
        self._require_login()
        test_response = self.client.post(self.url_detail, self.user_dict, format='json')
        self.assertTrue(status.is_client_error(test_response.status_code))
        self.assertEqual(test_response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertEqual(test_response.data, {'detail': 'Method "POST" not allowed.'})

    def test_retrieve_resource_patch_authenticated(self):
        """Patch field, then try and patch a protected field (username)"""
        self.test_retrieve_resource_authenticated()

        test_response = self.client.patch(self.url_detail, {'first_name': 'terrific new name'}, format='json')
        self.assertTrue(status.is_success(test_response.status_code))
        # serialize response.data (dict) to json str so can check if contains string
        self.assertIn('"first_name": "terrific new name"', json.dumps(test_response.data))

        # Attempt to patch protected field, and non-existant field
        test_response_2 = self.client.patch(self.url_detail, data={'username': 'cantchangethis'}, format='json')
        self.assertNotIn('"username": "cantchangethis"', json.dumps(test_response_2.data))
        test_response_3 = self.client.patch(self.url_detail, data={'usernamedoesntexist': 'new_username'}, format='json')
        self.assertNotIn('"usernamedoesntexist": "new_username"', json.dumps(test_response_3.data))
        # TODO These status codes aren't correct - both are returning 200 instead of 400







        # field = 'username'
        # patch_data = 'new_username'
        # test_response = self.client.patch(self.url_detail, {field: patch_data}, format='json')
        # print(test_response.data)
        # print(test_response.status_code)
        # # self.assertTrue(status.is_success(test_response.status_code))
        # # # serialize response.data (dict) to json str so can check if contains string
        # # self.assertIn(patch_data, json.dumps(test_response.data))

    def test_retrieve_resource_put(self):
        pass

            #
    # def test_login_unauthenticated(self):
    #     login_url = reverse('rest_framework:login')
    #     test_response = self.client.get(login_url)
    #     self.assertTrue(status.is_success(test_response.status_code))
    #
    # def test_login_redirect(self):
    #     self._require_login()
    #     login_url = reverse('rest_framework:login')
    #     test_response = self.client.get(login_url)
    #     # print(vars(test_response))
    #     # self.assertTrue(status.is_success(test_response.status_code))
    #     # TODO FINISH THIS TEST
    #
    #
    # def change_password_unauthenticated(self):
    #     # Endpoint exists
    #     change_password_url = reverse('user-change-password')
    #     test_response = self.client.get(change_password_url)
    #     self.assertTrue(status.is_success(test_response.status_code))
    #
    #     # Create new user
    #     test_response = self.client.post(self.url_create, self.user_dict, format='json')
    #     self.assertTrue(status.is_success(test_response.status_code))
    #     # verify exists
    #     self.assertEqual(User.objects.count(), 2)
    #
    #     # POST new password to username + email
    #     new_password_dict = {
    #         'email': "test@hotmail.com",
    #         'username': "test_user_2",
    #         'password': 'new_test',
    #         'confirm_password': 'new_test',
    #     }
    #
    #     test_response = self.client.post(change_password_url, new_password_dict, format='json')
    #     self.assertTrue(status.is_success(test_response.status_code))
    #
    #     # Send incorrect username/password combo
    #     new_password_dict['email'] = 'incorrectemail@hotmail.com'
    #     test_response = self.client.post(change_password_url, new_password_dict, format='json')
    #     self.assertTrue(status.is_client_error(test_response.status_code))
    #     # Send username does not exist
    #
    #     # Send malformed data
    #     new_password_dict['email'] = 'malformedemail'
    #     test_response = self.client.post(change_password_url, new_password_dict, format='json')
    #     self.assertTrue(status.is_client_error(test_response.status_code))
    #
    #
    # def change_password_authenticated(self):
    #     self._require_login()
    #     # Not sure what to do here - need to add the change password dialogue to the user profile thing...
    #     # Return a bound form if user is logged in?? Then sign them out?
    #     pass
    #
    #
    # def check_logout_template(self):
    #     self._require_login()
    #     test_response = self.client.get(reverse('rest_framework:logout'))
    #     self.assertTemplateUsed('user/django_auth/logout')


# class AdminUserTests(APITestCase):
#     url_list = reverse('user-list')
#     url_detail = reverse('user-detail')
#     pass

