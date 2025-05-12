import http
import os

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import resolve

from rpidrive.controllers.file import compress_files
from rpidrive.controllers.local_file import create_entry
from rpidrive.tests.helpers.setup import SetupContext
from rpidrive.views.ui_api.jobs import JobListView


class TestJobListView(TestCase):
    """Test job list view"""

    def setUp(self):
        self.url = "/drive/ui-api/jobs/"
        self.context = SetupContext()
        self.user = User.objects.create_user("z")

    def tearDown(self):
        self.context.cleanup()
        User.objects.all().delete()

    def test_url(self):
        """Test url"""
        self.assertEqual(JobListView, resolve(self.url).func.view_class)

    def test_get_1(self):
        """Test GET method"""
        text_fp_1 = os.path.join(self.context.root_path, "hehe.txt")
        with open(text_fp_1, "w+") as f_h:
            f_h.write("a")
        file_obj = create_entry(self.context.volume, self.context.root_file, text_fp_1)
        compress_files(
            self.context.admin,
            [str(file_obj.id)],
            self.context.root_file.id,
            "hehe.zip",
        )

        self.client.force_login(self.context.admin)
        response = self.client.get(self.url)
        self.assertEqual(http.HTTPStatus.OK, response.status_code)
        data = response.json()
        self.assertEqual(1, len(data["values"]))
        data = data["values"][0]
        self.assertTrue("id" in data)
        del data["id"]
        self.assertEqual(
            {
                "description": "hehe.zip",
                "progress": 0,
                "status": "In queue",
                "to_stop": False,
                "kind": "zip",
            },
            data,
        )

    def test_get_2(self):
        """Test GET method"""
        text_fp_1 = os.path.join(self.context.root_path, "hehe.txt")
        with open(text_fp_1, "w+") as f_h:
            f_h.write("a")
        file_obj = create_entry(self.context.volume, self.context.root_file, text_fp_1)
        compress_files(
            self.context.admin,
            [str(file_obj.id)],
            self.context.root_file.id,
            "hehe.zip",
        )

        self.client.force_login(self.user)
        response = self.client.get(self.url)
        self.assertEqual(http.HTTPStatus.OK, response.status_code)
        self.assertEqual({"values": []}, response.json())

    def test_get_3(self):
        """Test GET method"""
        response = self.client.get(self.url)
        self.assertEqual(http.HTTPStatus.FOUND, response.status_code)
        self.assertEqual(b"", response.content)

    def test_post_1(self):
        """Test POST method"""
        self.client.force_login(self.context.admin)
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
        self.client.force_login(self.context.admin)
        response = self.client.put(self.url)
        self.assertEqual(http.HTTPStatus.METHOD_NOT_ALLOWED, response.status_code)
        self.assertEqual(b"", response.content)

    def test_put_2(self):
        """Test PUT method"""
        response = self.client.put(self.url)
        self.assertEqual(http.HTTPStatus.FOUND, response.status_code)
        self.assertEqual(b"", response.content)

    def test_delete_1(self):
        """Test DELETE method"""
        self.client.force_login(self.context.admin)
        response = self.client.delete(self.url)
        self.assertEqual(http.HTTPStatus.METHOD_NOT_ALLOWED, response.status_code)
        self.assertEqual(b"", response.content)

    def test_delete_2(self):
        """Test DELETE method"""
        response = self.client.delete(self.url)
        self.assertEqual(http.HTTPStatus.FOUND, response.status_code)
        self.assertEqual(b"", response.content)
