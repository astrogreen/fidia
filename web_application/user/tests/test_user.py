import json, string, random
from django.conf import settings

from django.contrib.auth.models import User
from django.core.cache import cache

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


def pp(test_response):
    print('')
    print('-- Response --')
    print('Response Data ' + str(test_response.data))
    print('Status Code ' + str(test_response.status_code))
    print('-------------- ')


def is_json(myjson):
    try:
        json_object = json.loads(myjson)
    except ValueError:
        return False
    return True


def helper_new_user():
    """return new user dict"""

    def rand_string(length):
        """return random string"""
        return ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(length))

    email = rand_string(5)+'@'+rand_string(5)+'.com'

    user_dict = {
        'first_name': rand_string(10),
        'last_name': rand_string(10),
        'email': email,
        'username': rand_string(10),
        'password': 'test',
        'confirm_password': 'test',
    }

    return user_dict


class TestSetUp(APITestCase):
    """
    Mixin to add setup functionality
     Set up test_user_0 in db, user_dict is test_user_1 (though this can be overriden on the create_resource
     test with user_id, so that the throttling test can be run).
    """
    def setUp(self):
        # Clear the cache so no throttles will be active
        cache.clear()

        # Request Factor returns a request (useful for testing components that require request param)
        self.factory = APIRequestFactory()

        # Client returns a response (complete request-response cycle)
        self.client = APIClient()

        # Set up one user
        self.username = 'test_user_0'
        self.user = User.objects.create_user(first_name='test_first_name', last_name='test_last_name',
                                             username=self.username, email='test_user@test.com', password='test_password')
        self.user.save()
        self.url_detail = reverse('user-profile-detail', kwargs={'username': self.username})

        # Prepare new user dict
        self.user_dict = {
            'first_name': "another user",
            'last_name': "test",
            'email': "test@hotmail.com",
            'username': "test_user_1",
            'password': 'test',
            'confirm_password': 'test',
        }

    def _require_login(self):
        self.client.login(first_name='test_first_name', last_name='test_last_name',
                          username=self.username, email='test_user@test.com', password='test_password')


class CreateUserTests(TestSetUp, APITestCase):

    url_create = reverse('user-register')

    # CREATE (REGISTER)
    def test_create_resource_check_template(self):
        """ Check template used at /register/: 200 OK """
        test_response = self.client.get(self.url_create)
        self.assertTrue(status.is_success(test_response.status_code))
        self.assertTemplateUsed('user/register/register.html')
        self.assertEqual(test_response.status_code, status.HTTP_200_OK)

    def test_create_resource_unauthenticated(self):
        """ Unauthenticated users should be able to create a user: 201 CREATED """
        test_response = self.client.post(self.url_create, self.user_dict, format='json')
        self.assertTrue(status.is_success(test_response.status_code))
        self.assertEqual(test_response.status_code, status.HTTP_201_CREATED)

    def test_create_admin_resource_unauthenticated(self):
        """ Admin users cannot be created via this endpoint, create regular user: 201 CREATED """
        admin_dict = self.user_dict
        admin_dict['username'] = 'register_admin_user'
        admin_dict['is_staff'] = True
        test_response = self.client.post(self.url_create, admin_dict, format='json')

        self.assertTrue(status.is_success(test_response.status_code))
        self.assertEqual(test_response.status_code, status.HTTP_201_CREATED)

        attempted_admin_user = User.objects.get(username='register_admin_user')
        self.assertFalse(attempted_admin_user.is_staff)

    def test_create_resource_authenticated(self):
        """ Authenticated users shouldn't be able to register: 403 FORBIDDEN"""
        self._require_login()
        test_response = self.client.post(self.url_create, self.user_dict, format='json')
        self.assertTrue(status.is_client_error(test_response.status_code))
        self.assertEqual(test_response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn("You do not have permission to perform this action.", json.dumps(test_response.data))

    def test_create_resource_username_too_long(self):
        """ Send incorrect data: 400 BAD REQUEST """
        username_too_long = self.user_dict
        username_too_long['username'] = ''.join(random.choice(string.ascii_lowercase) for x in range(51))
        test_response = self.client.post(self.url_create, username_too_long, format='json')
        self.assertTrue(status.is_client_error(test_response.status_code))
        self.assertEqual(test_response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Please limit to 50 characters", json.dumps(test_response.data))

    def test_create_resource_username_exists(self):
        """ Send incorrect data: 409 CONFLICT """
        self.test_create_resource_unauthenticated()
        # Attempt to create a second (identical username)
        test_response = self.client.post(self.url_create, self.user_dict, format='json')
        self.assertTrue(status.is_client_error(test_response.status_code))
        self.assertEqual(test_response.status_code, status.HTTP_409_CONFLICT)
        self.assertIn("User test_user_1 already exists", json.dumps(test_response.data))

    def test_create_resource_email_exists(self):
        """ Send incorrect data: 409 CONFLICT """
        self.test_create_resource_unauthenticated()
        # Attempt to create a second (different username, identical email)
        same_email = self.user_dict
        same_email['username'] = 'this_user_has_already_registered_that_email'
        test_response = self.client.post(self.url_create, same_email, format='json')
        self.assertTrue(status.is_client_error(test_response.status_code))
        self.assertEqual(test_response.status_code, status.HTTP_409_CONFLICT)
        self.assertIn("already registered.", json.dumps(test_response.data))

    def test_create_resource_mismatched_passwords(self):
        """ Send incorrect data: 400 BAD REQUEST """
        password_mismatch_dict = self.user_dict
        password_mismatch_dict['password'] = "this_doesnt_match"
        test_response = self.client.post(self.url_create, password_mismatch_dict, format='json')
        self.assertTrue(status.is_client_error(test_response.status_code))
        self.assertEqual(test_response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Passwords do not match", json.dumps(test_response.data))

    def test_create_resource_malformed_data(self):
        """ Send malformed data: 400 BAD REQUEST """
        malformed_data = '{"malformed":"json"}'
        test_response = self.client.post(self.url_create, malformed_data,
                                         content_type="application/json")
        self.assertEqual(test_response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("This field is required.", json.dumps(test_response.data))

    def test_create_resource_bad_method(self):
        """ Request put and patch methods on creating new resource: 405 METHOD NOT ALLOWED """
        test_response = self.client.put(self.url_create, self.user_dict, format='json')
        self.assertTrue(status.is_client_error(test_response.status_code))
        # here, we also have to pass the string as valid json to compare (else " aren't properly escaped)
        self.assertIn(json.dumps('Method "PUT" not allowed.'), json.dumps(test_response.data))
        self.assertEqual(test_response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

        patch_data = self.user_dict.pop('last_name')
        test_response = self.client.patch(self.url_create, patch_data, format='json')
        self.assertTrue(status.is_client_error(test_response.status_code))
        self.assertEqual(test_response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertIn(json.dumps('Method "PATCH" not allowed.'), json.dumps(test_response.data))




class ThrottleTest(APITestCase):
    """
    Check throttling works, if it's activate on the particular view associate with the named url
    """
    url_create = reverse('user-register')

    def setUp(self):
        cache.clear()
        # Clear the cache from previous tests (if any)
        self.client = APIClient()
        self.user_dict = {
            'first_name': "another user",
            'last_name': "test",
            'email': "test@hotmail.com",
            'username': "test_user_1",
            'password': 'test',
            'confirm_password': 'test',
        }

    def test_create_resource_throttle(self):
        """
        Unauthenticated. Trigger throttled response
        """
        if 'anon' in settings.REST_FRAMEWORK['DEFAULT_THROTTLE_RATES']:
            throttle_rate = settings.REST_FRAMEWORK['DEFAULT_THROTTLE_RATES']['anon']
            integer_throttle_rate = throttle_rate.split('/day')[0]

            for i in range(int(integer_throttle_rate) + 2):

                user_info = self.user_dict
                # these both need to be unique
                user_info['username'] = 'test_user_'+str(i)
                user_info['email'] = 'test'+str(i)+'@hotmail.com'
                test_response = self.client.post(self.url_create, user_info, format='json')

                if i < (int(integer_throttle_rate)):
                    self.assertTrue(status.is_success(test_response.status_code))
                    self.assertEqual(test_response.status_code, status.HTTP_201_CREATED)

                else:
                    self.assertTrue(status.is_client_error(test_response.status_code))
                    self.assertEqual(test_response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
                    self.assertIn("Request was throttled. Expected available in 86400 seconds.", json.dumps(test_response.data))




class UserProfileTests(TestSetUp, APITestCase):
    """
    /accounts/username profile.
    Retrieve:Get Update:Put/Patch Destroy:Delete
    """

    # RETRIEVE (ACCOUNTS/USERNAME)
    def test_retrieve_resource_check_template(self):
        """ Check template used at /accounts/ 200 OK """
        self._require_login()
        test_response = self.client.get(self.url_detail)
        self.assertTrue(status.is_success(test_response.status_code))
        self.assertEqual(test_response.status_code, status.HTTP_200_OK)
        self.assertTemplateUsed('user/profile/profile.html')

    def test_retrieve_resource_unauthenticated(self):
        """ Unauthenticated users shouldn't see username's details: 403 FORBIDDEN """
        test_response = self.client.get(self.url_detail)
        self.assertTrue(status.is_client_error(test_response.status_code))
        self.assertEqual(test_response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn("Authentication credentials were not provided.", json.dumps(test_response.data))

    def test_retrieve_resource_authenticated(self):
        """
        Authenticated users get profile details /accounts/username/: 200 OK
        """
        self._require_login()
        test_response = self.client.get(self.url_detail)
        self.assertEqual(test_response.data,
                         {'last_name': 'test_last_name', 'username': self.username, 'first_name': 'test_first_name',
                          'query': [], 'email': 'test_user@test.com'})
        self.assertTrue(status.is_success(test_response.status_code))
        self.assertEqual(test_response.status_code, status.HTTP_200_OK)

    def test_retrieve_resource_incorrect_method(self):
        """Authenticated user post to /accounts/username: 405 METHOD NOT ALLOWED"""
        self._require_login()
        test_response = self.client.post(self.url_detail, self.user_dict, format='json')
        self.assertTrue(status.is_client_error(test_response.status_code))
        self.assertEqual(test_response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertEqual(test_response.data, {'detail': 'Method "POST" not allowed.'})

    def test_profile_query_history(self):
        url_query_create = reverse('query-create-list')
        self._require_login()
        data = {
            "title": "test_title",
            "SQL": "SELECT * FROM SAMI LIMIT 1",
        }
        test_response_query = self.client.post(url_query_create, data, format='json')
        self.assertEqual(test_response_query.status_code, status.HTTP_201_CREATED)

        test_response = self.client.get(self.url_detail)
        query_count = len(test_response.data['query'])
        self.assertEqual(query_count, 1)
        self.assertTrue(status.is_success(test_response.status_code))
        self.assertEqual(test_response.status_code, status.HTTP_200_OK)

    def test_access_query_history_another_user(self):
        """ Attempt to access query history of another user: 404 NOT FOUND"""
        # Create secondary user (test_user_1)
        url_create = reverse('user-register')
        test_response = self.client.post(url_create, self.user_dict, format='json')
        self.assertTrue(status.is_success(test_response.status_code))
        self.assertEqual(test_response.status_code, status.HTTP_201_CREATED)

        # Login as test_user_1
        url_query_history = reverse('query-list') + '1/'
        self.client.login(username=self.user_dict['username'], password=self.user_dict['password'])

        # Attempt to view query-history/1/ made by test_user_0 in previous test
        test_response = self.client.get(url_query_history)
        self.assertTrue(status.is_client_error(test_response.status_code))
        self.assertEqual(test_response.status_code, status.HTTP_404_NOT_FOUND)

    # UPDATE
    def test_put_resource(self):
        """Put request: 200 OK"""
        self.test_retrieve_resource_authenticated()
        test_response = self.client.patch(self.url_detail, self.user_dict, format='json')
        self.assertTrue(status.is_success(test_response.status_code))
        self.assertEqual(test_response.status_code, status.HTTP_200_OK)
        self.assertIn('"first_name": "another user"', json.dumps(test_response.data))

    def test_patch_authenticated(self):
        """Patch field, then try and patch a protected field (username): 400 BAD REQUEST"""
        self.test_retrieve_resource_authenticated()

        test_response = self.client.patch(self.url_detail, {'first_name': 'terrific new name'}, format='json')
        self.assertTrue(status.is_success(test_response.status_code))
        self.assertEqual(test_response.status_code, status.HTTP_200_OK)
        # serialize response.data (dict) to json str so can check if contains string
        self.assertIn('"first_name": "terrific new name"', json.dumps(test_response.data))

    def test_patch_bad_request_authenticated(self):
        """Patch a protected field (username): 400 BAD REQUEST"""
        # TODO These status codes aren't correct - both are returning 200 instead of 400
        self._require_login()
        # Attempt to patch protected field, and non-existant field
        test_response_2 = self.client.patch(self.url_detail, data={'username': 'cantchangethis'}, format='json')
        self.assertNotIn('"username": "cantchangethis"', json.dumps(test_response_2.data))

        # test_response_3 = self.client.patch(self.url_detail, data={'usernamedoesntexist': 'new_username'}, format='json')
        # self.assertNotIn('"usernamedoesntexist": "new_username"', json.dumps(test_response_3.data))

    # DESTROY
    def test_delete_user_authenticated(self):
        """
        Authenticated user can delete their own account
        Vary the ACCEPT header (application/json, text/html)
        """
        # APPLICATION/JSON

        # Create user
        url_create = CreateUserTests.url_create
        new_user_dict = helper_new_user()
        test_response = self.client.post(url_create, new_user_dict, format='json')
        self.assertEqual(test_response.status_code, status.HTTP_201_CREATED)

        # Login as user
        self.client.login(username=new_user_dict['username'], password=new_user_dict['password'])

        # Check user profile exists
        url_detail = reverse('user-profile-detail', kwargs={'username': new_user_dict['username']})
        test_response = self.client.get(url_detail)
        self.assertEqual(test_response.status_code, status.HTTP_200_OK)

        # Delete account
        # This is coerced to 200 when returning html content else page won't display in browser...
        # https://github.com/tomchristie/django-rest-framework/issues/3935
        # Force the accept header to json (by passing browser restrictions)

        test_response = self.client.delete(url_detail, HTTP_ACCEPT='application/json')
        self.assertEqual(test_response.status_code, status.HTTP_204_NO_CONTENT)

        # User can no longer access this profile
        test_response = self.client.get(url_detail)
        self.assertEqual(test_response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn('"detail": "Authentication credentials were not provided."', json.dumps(test_response.data))

        # TEXT/HTML
        # Test for template tag injection of detailed message if ACCEPT = html
        new_user_dict = helper_new_user()
        test_response = self.client.post(url_create, new_user_dict, format='json')
        self.assertEqual(test_response.status_code, status.HTTP_201_CREATED)
        self.client.login(username=new_user_dict['username'], password=new_user_dict['password'])
        url_detail = reverse('user-profile-detail', kwargs={'username': new_user_dict['username']})
        test_response = self.client.delete(url_detail, HTTP_ACCEPT='text/html')

        # status code here is 200 (else browser wouldn't display, request.data is empty) but our template tag
        # handling the status info injects a message for No Content.
        self.assertIn("No Content", str(test_response.content))

        # User can no longer access this profile
        test_response = self.client.get(url_detail)
        self.assertEqual(test_response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn('"detail": "Authentication credentials were not provided."', json.dumps(test_response.data))


class AdminUserTests(TestSetUp, APITestCase):

    def test_get_user_admin(self):
        """
        Admin user can see all users: 200 OK
        """
        url_list = reverse('user-list')

        admin_user = User.objects.create_user(first_name='test_first_name', last_name='test_last_name',
                                              username='test_admin_user_0', email='test_user@test.com',
                                              password='test_password')
        admin_user.is_staff = True
        admin_user.save()
        self.client.login(username='test_admin_user_0', password='test_password')

        test_response = self.client.get(url_list)
        self.assertEqual(test_response.status_code, status.HTTP_200_OK)

    def test_get_user_not_admin(self):
        pass


class UserChangePasswordTest(TestSetUp, APITestCase):

    def test_authentication(self):
        pass

    def test_tempalate(self):
        pass

    def test_email(self):
        pass


class UserAuthBrowsableAPI(TestSetUp, APITestCase):
    """
    Check templates, redirects,
    """

    def test_login(self):

        pass

# TODO redirect and login on registration

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




