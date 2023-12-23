import http

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import resolve

from rpidrive.views.ui_api.users import UserCreateView


class TestUserCreateView(TestCase):
    """Test UserCreateView"""

    def setUp(self):
        self.url = "/drive/ui-api/users/create"
        self.admin_user = User.objects.create_superuser("a")
        self.user = User.objects.create_user("z")

    def tearDown(self):
        User.objects.all().delete()

    def test_url(self):
        """Test url"""
        self.assertEqual(UserCreateView, resolve(self.url).func.view_class)

    def test_get(self):
        """Test GET method"""
        self.client.force_login(self.admin_user)
        response = self.client.get(self.url)
        self.assertEqual(http.HTTPStatus.METHOD_NOT_ALLOWED, response.status_code)
        self.assertEqual(b"", response.content)

    def test_put(self):
        """Test PUT method"""
        self.client.force_login(self.admin_user)
        response = self.client.put(self.url)
        self.assertEqual(http.HTTPStatus.METHOD_NOT_ALLOWED, response.status_code)
        self.assertEqual(b"", response.content)

    def test_delete(self):
        """Test DELETE method"""
        self.client.force_login(self.admin_user)
        response = self.client.delete(self.url)
        self.assertEqual(http.HTTPStatus.METHOD_NOT_ALLOWED, response.status_code)
        self.assertEqual(b"", response.content)

    def test_post(self):
        """Test POST method"""
        post_data = {
            "username": "gg",
            "email": "aaa@aaa.com",
            "password": "XDXD",
            "is_superuser": False,
            "is_active": True,
            "first_name": "f",
            "last_name": "l",
        }
        self.client.force_login(self.admin_user)
        response = self.client.post(self.url, post_data, "application/json")
        self.assertEqual(http.HTTPStatus.CREATED, response.status_code)

        data = response.json()
        created_user = User.objects.last()
        self.assertEqual(3, User.objects.count())
        self.assertEqual(created_user.id, data["id"])
        self.assertEqual(post_data["username"], created_user.username)
        self.assertEqual(post_data["email"], created_user.email)
        self.assertTrue(created_user.check_password(post_data["password"]))
        self.assertEqual(post_data["is_superuser"], created_user.is_superuser)
        self.assertEqual(post_data["is_active"], created_user.is_active)
        self.assertEqual(post_data["first_name"], created_user.first_name)
        self.assertEqual(post_data["last_name"], created_user.last_name)

    def test_post_2(self):
        """Test POST method (No first name & last name)"""
        post_data = {
            "username": "gg",
            "email": "aaa@aaa.com",
            "password": "XDXD",
            "is_superuser": False,
            "is_active": True,
        }
        self.client.force_login(self.admin_user)
        response = self.client.post(self.url, post_data, "application/json")
        self.assertEqual(http.HTTPStatus.CREATED, response.status_code)

        data = response.json()
        created_user = User.objects.last()
        self.assertEqual(3, User.objects.count())
        self.assertEqual(created_user.id, data["id"])
        self.assertEqual(post_data["username"], created_user.username)
        self.assertEqual(post_data["email"], created_user.email)
        self.assertTrue(created_user.check_password(post_data["password"]))
        self.assertEqual(post_data["is_superuser"], created_user.is_superuser)
        self.assertEqual(post_data["is_active"], created_user.is_active)
        self.assertEqual("", created_user.first_name)
        self.assertEqual("", created_user.last_name)

    def test_post_normal_user(self):
        """Test POST method (Normal user)"""
        post_data = {
            "username": "gg",
            "email": "aaa@aaa.com",
            "password": "XDXD",
            "is_superuser": False,
            "is_active": True,
        }
        self.client.force_login(self.user)
        response = self.client.post(self.url, post_data, "application/json")
        self.assertEqual(http.HTTPStatus.FORBIDDEN, response.status_code)
        self.assertEqual({"error": "No permission."}, response.json())
        self.assertEqual(2, User.objects.count())

    def test_post_no_login(self):
        """Test POST method (No login)"""
        post_data = {
            "username": "gg",
            "email": "aaa@aaa.com",
            "password": "XDXD",
            "is_superuser": False,
            "is_active": True,
        }
        response = self.client.post(self.url, post_data, "application/json")
        self.assertEqual(http.HTTPStatus.FOUND, response.status_code)
        self.assertEqual(b"", response.content)
