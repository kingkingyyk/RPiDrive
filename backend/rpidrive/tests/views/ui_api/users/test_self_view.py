import http

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import resolve

from rpidrive.views.ui_api.users import UserSelfView


class TestUserSelfView(TestCase):
    """Test UserSelfView"""

    def setUp(self):
        self.url = "/drive/ui-api/users/self"
        self.admin_user = User.objects.create_superuser(
            "a",
            "a@a.com",
            first_name="b",
            last_name="c",
        )
        self.user = User.objects.create_user(
            "z",
            "z@x.com",
            "gg!!",
            first_name="x",
            last_name="y",
        )

    def tearDown(self):
        User.objects.all().delete()

    def test_url(self):
        """Test url"""
        self.assertEqual(UserSelfView, resolve(self.url).func.view_class)

    def test_post_1(self):
        """Test POST method"""
        self.client.force_login(self.user)
        response = self.client.post(self.url)
        self.assertEqual(http.HTTPStatus.METHOD_NOT_ALLOWED, response.status_code)
        self.assertEqual(b"", response.content)

    def test_post_2(self):
        """Test POST method (No login)"""
        response = self.client.post(self.url)
        self.assertEqual(http.HTTPStatus.FOUND, response.status_code)
        self.assertEqual(b"", response.content)

    def test_put_1(self):
        """Test PUT method"""
        self.client.force_login(self.user)
        response = self.client.put(self.url)
        self.assertEqual(http.HTTPStatus.METHOD_NOT_ALLOWED, response.status_code)
        self.assertEqual(b"", response.content)

    def test_put_2(self):
        """Test PUT method (No login)"""
        response = self.client.put(self.url)
        self.assertEqual(http.HTTPStatus.FOUND, response.status_code)
        self.assertEqual(b"", response.content)

    def test_delete_1(self):
        """Test DELETE method"""
        self.client.force_login(self.user)
        response = self.client.delete(self.url)
        self.assertEqual(http.HTTPStatus.METHOD_NOT_ALLOWED, response.status_code)
        self.assertEqual(b"", response.content)

    def test_delete_2(self):
        """Test DELETE method (No login)"""
        response = self.client.delete(self.url)
        self.assertEqual(http.HTTPStatus.FOUND, response.status_code)
        self.assertEqual(b"", response.content)

    def test_get_1(self):
        """Test GET method"""
        self.client.force_login(self.admin_user)
        response = self.client.get(self.url)
        self.assertEqual(http.HTTPStatus.OK, response.status_code)
        self.assertEqual(
            {
                "id": self.admin_user.id,
                "username": self.admin_user.username,
                "first_name": self.admin_user.first_name,
                "last_name": self.admin_user.last_name,
                "is_superuser": self.admin_user.is_superuser,
                "is_active": self.admin_user.is_active,
                "email": self.admin_user.email,
            },
            response.json(),
        )
        self.client.logout()

        self.client.force_login(self.user)
        response = self.client.get(self.url)
        self.assertEqual(http.HTTPStatus.OK, response.status_code)
        self.assertEqual(
            {
                "id": self.user.id,
                "username": self.user.username,
                "first_name": self.user.first_name,
                "last_name": self.user.last_name,
                "is_superuser": self.user.is_superuser,
                "is_active": self.user.is_active,
                "email": self.user.email,
            },
            response.json(),
        )
        self.client.logout()

    def test_get_2(self):
        """Test GET method (No login)"""
        response = self.client.get(self.url)
        self.assertEqual(http.HTTPStatus.FOUND, response.status_code)
        self.assertEqual(b"", response.content)
