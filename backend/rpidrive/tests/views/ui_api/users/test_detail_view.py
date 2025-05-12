import http

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import resolve

from rpidrive.views.ui_api.users import UserDetailView


class TestUserDetailView(TestCase):
    """Test UserDetailView"""

    def setUp(self):
        self.url = "/drive/ui-api/users/"
        self.admin_user = User.objects.create_superuser(
            "a",
            email="a@a.com",
            first_name="b",
            last_name="c",
        )
        self.user = User.objects.create_user(
            "z",
            email="z@x.com",
            first_name="x",
            last_name="y",
        )

    def tearDown(self):
        User.objects.all().delete()

    def test_url(self):
        """Test url"""
        self.assertEqual(UserDetailView, resolve(f"{self.url}123").func.view_class)

    def test_get_1(self):
        """Test GET method (Admin can read all)"""
        self.client.force_login(self.admin_user)
        response = self.client.get(f"{self.url}{self.admin_user.id}")
        self.assertEqual(http.HTTPStatus.OK, response.status_code)
        self.assertEqual(
            {
                "id": self.admin_user.pk,
                "username": self.admin_user.username,
                "first_name": self.admin_user.first_name,
                "last_name": self.admin_user.last_name,
                "is_superuser": self.admin_user.is_superuser,
                "is_active": self.admin_user.is_active,
                "email": self.admin_user.email,
            },
            response.json(),
        )

        response = self.client.get(f"{self.url}{self.user.id}")
        self.assertEqual(http.HTTPStatus.OK, response.status_code)
        self.assertEqual(
            {
                "id": self.user.pk,
                "username": self.user.username,
                "first_name": self.user.first_name,
                "last_name": self.user.last_name,
                "is_superuser": self.user.is_superuser,
                "is_active": self.user.is_active,
                "email": self.user.email,
            },
            response.json(),
        )

        response = self.client.get(f"{self.url}{self.user.pk+100}")
        self.assertEqual(http.HTTPStatus.NOT_FOUND, response.status_code)
        self.assertEqual({"error": "User not found."}, response.json())

    def test_get_2(self):
        """Test GET method (Only can get own)"""
        self.client.force_login(self.user)
        response = self.client.get(f"{self.url}{self.admin_user.id}")
        self.assertEqual(http.HTTPStatus.FORBIDDEN, response.status_code)
        self.assertEqual({"error": "No permission."}, response.json())

        response = self.client.get(f"{self.url}{self.user.id}")
        self.assertEqual(http.HTTPStatus.OK, response.status_code)
        self.assertEqual(
            {
                "id": self.user.pk,
                "username": self.user.username,
                "first_name": self.user.first_name,
                "last_name": self.user.last_name,
                "is_superuser": self.user.is_superuser,
                "is_active": self.user.is_active,
                "email": self.user.email,
            },
            response.json(),
        )

        response = self.client.get(f"{self.url}{self.user.pk+100}")
        self.assertEqual(http.HTTPStatus.FORBIDDEN, response.status_code)
        self.assertEqual({"error": "No permission."}, response.json())

    def test_get_3(self):
        """Test GET method (No login)"""
        response = self.client.get(f"{self.url}{self.admin_user.id}")
        self.assertEqual(http.HTTPStatus.FOUND, response.status_code)
        self.assertEqual(b"", response.content)

        response = self.client.get(f"{self.url}{self.user.id}")
        self.assertEqual(http.HTTPStatus.FOUND, response.status_code)
        self.assertEqual(b"", response.content)

        response = self.client.get(f"{self.url}{self.user.pk+100}")
        self.assertEqual(http.HTTPStatus.FOUND, response.status_code)
        self.assertEqual(b"", response.content)

    def test_put_method_1(self):
        """Test PUT method"""
        self.client.force_login(self.admin_user)
        response = self.client.put(f"{self.url}{self.admin_user.id}")
        self.assertEqual(http.HTTPStatus.METHOD_NOT_ALLOWED, response.status_code)
        self.assertEqual(b"", response.content)

    def test_put_method_2(self):
        """Test PUT method (No login)"""
        response = self.client.put(f"{self.url}{self.admin_user.id}")
        self.assertEqual(http.HTTPStatus.FOUND, response.status_code)
        self.assertEqual(b"", response.content)

    def test_post_method_1(self):
        """Test POST method (Admin changes self)"""
        post_data = {
            "email": "aaa@aaa.com",
            "password": "XDXD",
            "is_superuser": True,
            "is_active": True,
            "first_name": "first",
            "last_name": "last",
        }

        self.client.force_login(self.admin_user)
        response = self.client.post(
            f"{self.url}{self.admin_user.id}",
            post_data,
            "application/json",
        )
        self.assertEqual(http.HTTPStatus.OK, response.status_code)
        self.assertEqual({}, response.json())

        self.admin_user.refresh_from_db()
        self.assertEqual(post_data["email"], self.admin_user.email)
        self.assertTrue(self.admin_user.check_password(post_data["password"]))
        self.assertEqual(post_data["first_name"], self.admin_user.first_name)
        self.assertEqual(post_data["last_name"], self.admin_user.last_name)

    def test_post_method_2(self):
        """Test POST method (Keep password)"""
        self.admin_user.set_password("@!@@")
        self.admin_user.save(update_fields=["password"])

        post_data = {
            "email": "aaa@aaa.com",
            "password": None,
            "is_superuser": True,
            "is_active": True,
        }
        self.client.force_login(self.admin_user)
        response = self.client.post(
            f"{self.url}{self.admin_user.id}",
            post_data,
            "application/json",
        )
        self.assertEqual(http.HTTPStatus.OK, response.status_code)
        self.assertEqual({}, response.json())

        self.admin_user.refresh_from_db()
        self.assertTrue(self.admin_user.check_password("@!@@"))

    def test_post_method_3(self):
        """Test POST method (Admin set self to normal)"""
        post_data = {
            "email": "aaa@aaa.com",
            "password": None,
            "is_superuser": False,
            "is_active": True,
        }
        self.client.force_login(self.admin_user)
        response = self.client.post(
            f"{self.url}{self.admin_user.id}",
            post_data,
            "application/json",
        )
        self.assertEqual(http.HTTPStatus.BAD_REQUEST, response.status_code)
        self.assertEqual(
            {"error": "Can't upgrade/downgrade yourself."}, response.json()
        )
        self.admin_user.refresh_from_db()
        self.assertTrue(self.admin_user.is_superuser)

    def test_post_method_4(self):
        """Test POST method (Admin deactivates self)"""
        post_data = {
            "email": "aaa@aaa.com",
            "password": None,
            "is_superuser": True,
            "is_active": False,
        }
        self.client.force_login(self.admin_user)
        response = self.client.post(
            f"{self.url}{self.admin_user.id}",
            post_data,
            "application/json",
        )
        self.assertEqual(http.HTTPStatus.BAD_REQUEST, response.status_code)
        self.assertEqual({"error": "Can't deactivate yourself."}, response.json())
        self.admin_user.refresh_from_db()
        self.assertTrue(self.admin_user.is_active)

    def test_post_method_5(self):
        """Test POST method (Admin changes other user)"""
        post_data = {
            "email": "aaa@aaa.com",
            "password": "XDXD",
            "is_superuser": True,
            "is_active": False,
            "first_name": "first",
            "last_name": "last",
        }

        self.client.force_login(self.admin_user)
        response = self.client.post(
            f"{self.url}{self.user.id}",
            post_data,
            "application/json",
        )
        self.assertEqual(http.HTTPStatus.OK, response.status_code)
        self.assertEqual({}, response.json())

        self.user.refresh_from_db()
        self.assertEqual(post_data["email"], self.user.email)
        self.assertTrue(self.user.check_password(post_data["password"]))
        self.assertEqual(post_data["first_name"], self.user.first_name)
        self.assertEqual(post_data["last_name"], self.user.last_name)
        self.assertTrue(self.user.is_superuser)
        self.assertFalse(self.user.is_active)

    def test_post_method_6(self):
        """Test POST method (User changes himself)"""
        post_data = {
            "email": "aaa@aaa.com",
            "password": "XDXD",
            "is_superuser": False,
            "is_active": True,
            "first_name": "first",
            "last_name": "last",
        }

        self.client.force_login(self.user)
        response = self.client.post(
            f"{self.url}{self.user.id}",
            post_data,
            "application/json",
        )
        self.assertEqual(http.HTTPStatus.OK, response.status_code)
        self.assertEqual({}, response.json())

        self.user.refresh_from_db()
        self.assertEqual(post_data["email"], self.user.email)
        self.assertTrue(self.user.check_password(post_data["password"]))
        self.assertEqual(post_data["first_name"], self.user.first_name)
        self.assertEqual(post_data["last_name"], self.user.last_name)

    def test_post_method_7(self):
        """Test POST method (User changes admin)"""
        post_data = {
            "email": "aaa@aaa.com",
            "password": "XDXD",
            "is_superuser": True,
            "is_active": True,
            "first_name": "first",
            "last_name": "last",
        }

        self.client.force_login(self.user)
        response = self.client.post(
            f"{self.url}{self.admin_user.id}",
            post_data,
            "application/json",
        )
        self.assertEqual(http.HTTPStatus.FORBIDDEN, response.status_code)
        self.assertEqual({"error": "No permission."}, response.json())

        self.admin_user.refresh_from_db()
        self.assertEqual("a@a.com", self.admin_user.email)
        self.assertEqual("b", self.admin_user.first_name)
        self.assertEqual("c", self.admin_user.last_name)

    def test_post_method_8(self):
        """Test POST method (No login changes admin)"""
        post_data = {
            "email": "aaa@aaa.com",
            "password": "XDXD",
            "is_superuser": True,
            "is_active": True,
            "first_name": "first",
            "last_name": "last",
        }

        response = self.client.post(
            f"{self.url}{self.admin_user.id}",
            post_data,
            "application/json",
        )
        self.assertEqual(http.HTTPStatus.FOUND, response.status_code)
        self.assertEqual(b"", response.content)

        self.admin_user.refresh_from_db()
        self.assertEqual("a@a.com", self.admin_user.email)
        self.assertEqual("b", self.admin_user.first_name)
        self.assertEqual("c", self.admin_user.last_name)

    def test_delete_1(self):
        """Test DELETE method (Admin deletes self)"""
        self.client.force_login(self.admin_user)
        response = self.client.delete(f"{self.url}{self.admin_user.id}")
        self.assertEqual(http.HTTPStatus.BAD_REQUEST, response.status_code)
        self.assertEqual({"error": "Can't delete yourself."}, response.json())
        self.assertEqual(2, User.objects.count())

    def test_delete_2(self):
        """Test DELETE method (Admin deletes other user)"""
        self.client.force_login(self.admin_user)
        response = self.client.delete(f"{self.url}{self.user.id}")
        self.assertEqual(http.HTTPStatus.OK, response.status_code)
        self.assertEqual({}, response.json())
        self.assertEqual(1, User.objects.count())
        self.assertEqual(self.admin_user, User.objects.first())

    def test_delete_3(self):
        """Test DELETE method (Other user deletes admin)"""
        self.client.force_login(self.user)
        response = self.client.delete(f"{self.url}{self.user.id}")
        self.assertEqual(http.HTTPStatus.FORBIDDEN, response.status_code)
        self.assertEqual({"error": "No permission."}, response.json())
        self.assertEqual(2, User.objects.count())
