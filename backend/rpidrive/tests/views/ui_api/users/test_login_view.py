import http

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import resolve

from rpidrive.views.decorators.mixins import BruteForceProtectMixin
from rpidrive.views.ui_api.users import UserLoginView


class TestUserLoginView(TestCase):
    """Test UserLoginView"""

    def setUp(self):
        self.url = "/drive/ui-api/users/login"
        self.user = User.objects.create_user(
            "z",
            "z@x.com",
            "gg!!",
            first_name="x",
            last_name="y",
        )

    def tearDown(self):
        User.objects.all().delete()
        BruteForceProtectMixin.reset()

    def test_url(self):
        """Test url"""
        self.assertEqual(UserLoginView, resolve(self.url).func.view_class)

    def test_get(self):
        """Test GET method"""
        response = self.client.get(self.url)
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

    def test_post_1(self):
        """Test POST method"""
        response = self.client.post(
            self.url, {"username": "z", "password": "gg!!"}, "application/json"
        )
        self.assertEqual(http.HTTPStatus.OK, response.status_code)
        self.assertEqual({}, response.json())
        self.assertEqual(3, len(self.client.session.keys()))

    def test_post_2(self):
        """Test POST method (Wrong login)"""
        response = self.client.post(
            self.url, {"username": "z", "password": "rip"}, "application/json"
        )
        self.assertEqual(http.HTTPStatus.UNAUTHORIZED, response.status_code)
        self.assertEqual({"error": "Invalid username/password"}, response.json())

    def test_post_3(self):
        """Test POST method (Block spam login)"""
        for count in range(10):
            response = self.client.post(
                self.url, {"username": "z", "password": "rip"}, "application/json"
            )
            if count < 5:
                self.assertEqual(http.HTTPStatus.UNAUTHORIZED, response.status_code)
                self.assertEqual(
                    {"error": "Invalid username/password"}, response.json()
                )
            else:
                self.assertEqual(http.HTTPStatus.FORBIDDEN, response.status_code)
                self.assertEqual(
                    {
                        "error": "Request blocked temporarily due to too many failed attempts!"
                    },
                    response.json(),
                )
