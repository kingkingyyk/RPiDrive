import http

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import resolve

from rpidrive.views.ui_api.users import UserLoggedInView


class TestCheckLoginView(TestCase):
    """Test CheckLoginView"""

    def setUp(self):
        self.url = "/drive/ui-api/users/check"
        self.user = User.objects.create_user("z")

    def tearDown(self):
        User.objects.all().delete()

    def test_url(self):
        """Test url"""
        self.assertEqual(UserLoggedInView, resolve(self.url).func.view_class)

    def test_get_no_login(self):
        """Test GET method (No login)"""
        response = self.client.get(self.url)
        self.assertEqual(http.HTTPStatus.FORBIDDEN, response.status_code)
        self.assertEqual({"flag": False}, response.json())

    def test_get(self):
        """Test GET method"""
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        self.assertEqual(http.HTTPStatus.OK, response.status_code)
        self.assertEqual({"flag": True}, response.json())

    def test_post(self):
        """Test POST method"""
        response = self.client.post(self.url)
        self.assertEqual(http.HTTPStatus.METHOD_NOT_ALLOWED, response.status_code)
        self.assertEqual(b"", response.content)

    def test_put(self):
        """Test PUT method"""
        response = self.client.put(self.url)
        self.assertEqual(http.HTTPStatus.METHOD_NOT_ALLOWED, response.status_code)
        self.assertEqual(b"", response.content)

    def test_delete(self):
        """Test DELETE method"""
        response = self.client.delete(self.url)
        self.assertEqual(http.HTTPStatus.METHOD_NOT_ALLOWED, response.status_code)
        self.assertEqual(b"", response.content)
