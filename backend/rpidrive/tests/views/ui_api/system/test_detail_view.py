import http

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import resolve

from rpidrive.views.ui_api.system import SystemDetailView


class TestSystemDetailView(TestCase):
    """Test system detail view"""

    def setUp(self):
        self.url = "/drive/ui-api/system/details"
        self.admin_user = User.objects.create_superuser("z")
        self.other_user = User.objects.create_user("a")

    def tearDown(self):
        User.objects.all().delete()

    def test_url(self):
        """Test url"""
        self.assertEqual(SystemDetailView, resolve(self.url).func.view_class)

    def test_get_no_login(self):
        """Test GET method (No login)"""
        response = self.client.get(self.url)
        self.assertEqual(http.HTTPStatus.FOUND, response.status_code)
        self.assertEqual(b"", response.content)

    def test_get_non_admin(self):
        """Test GET method (No login)"""
        self.client.force_login(self.other_user)
        response = self.client.get(self.url)
        self.assertEqual(http.HTTPStatus.FORBIDDEN, response.status_code)
        self.assertEqual({"error": ""}, response.json())

    def test_get(self):
        """Test GET method"""
        self.client.force_login(self.admin_user)
        response = self.client.get(self.url)
        self.assertEqual(http.HTTPStatus.OK, response.status_code)
        data = response.json()

        self.assertTrue("cpu" in data)
        self.assertTrue("model" in data["cpu"])
        self.assertTrue("cores" in data["cpu"])
        self.assertTrue("frequency" in data["cpu"])
        self.assertTrue("usage" in data["cpu"])

        self.assertTrue("memory" in data)
        self.assertTrue("total" in data["memory"])
        self.assertTrue("used" in data["memory"])
        self.assertTrue("usage" in data["memory"])

        self.assertTrue("disks" in data)
        self.assertGreater(len(data["disks"]), 0)

        self.assertTrue("environment" in data)
        self.assertGreater(len(data["environment"]), 0)

    def test_post(self):
        """Test POST method"""
        self.client.force_login(self.admin_user)
        response = self.client.post(self.url)
        self.assertEqual(http.HTTPStatus.METHOD_NOT_ALLOWED, response.status_code)

    def test_put(self):
        """Test PUT method"""
        self.client.force_login(self.admin_user)
        response = self.client.put(self.url)
        self.assertEqual(http.HTTPStatus.METHOD_NOT_ALLOWED, response.status_code)

    def test_delete(self):
        """Test DELETE method"""
        self.client.force_login(self.admin_user)
        response = self.client.delete(self.url)
        self.assertEqual(http.HTTPStatus.METHOD_NOT_ALLOWED, response.status_code)
