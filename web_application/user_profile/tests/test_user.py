from django.test import TestCase
from rest_framework.test import APIRequestFactory, APITestCase, APIClient, force_authenticate
from rest_framework import status, response
from rest_framework.reverse import reverse
from django.contrib.auth.models import User

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