import http
import os
import uuid
from datetime import timedelta

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import resolve
from django.utils import timezone

from rpidrive.controllers.file import share_file
from rpidrive.controllers.local_file import create_entry
from rpidrive.tests.helpers.setup import SetupContext
from rpidrive.views.ui_api.files import FileQAView


class TestFileQAView(TestCase):
    """Test FileMoveView"""

    def setUp(self):
        self.url = "/drive/quick-access"
        self.context = SetupContext()
        self.user = User.objects.create_user("z")

    def tearDown(self):
        self.context.cleanup()
        User.objects.all().delete()

    def test_url(self):
        """Test url"""
        self.assertEqual(FileQAView, resolve(self.url).func.view_class)

    def test_get_1(self):
        """Test GET method"""
        fp_1 = os.path.join(self.context.root_path, "song1.m4a")
        with open(fp_1, "w+") as f_h:
            f_h.write("a")
        file_1_obj = create_entry(self.context.volume, self.context.root_file, fp_1)
        link = share_file(self.context.admin, file_1_obj.id)

        response = self.client.get(self.url, {"key": link.id})
        self.assertEqual(http.HTTPStatus.OK, response.status_code)
        self.assertEqual(b"a", b"".join(response.streaming_content))

    def test_get_2(self):
        """Test GET method (Expired)"""
        fp_1 = os.path.join(self.context.root_path, "song1.m4a")
        with open(fp_1, "w+") as f_h:
            f_h.write("a")
        file_1_obj = create_entry(self.context.volume, self.context.root_file, fp_1)
        link = share_file(self.context.admin, file_1_obj.id)
        link.expire_time = timezone.now() - timedelta(minutes=1)
        link.save()

        response = self.client.get(self.url, {"key": link.id})
        self.assertEqual(http.HTTPStatus.NOT_FOUND, response.status_code)
        self.assertEqual({"error": "Key not found."}, response.json())

    def test_get_3(self):
        """Test GET method (Invalid key)"""
        response = self.client.get(self.url)
        self.assertEqual(http.HTTPStatus.NOT_FOUND, response.status_code)
        self.assertEqual({"error": "Key not found."}, response.json())

        response = self.client.get(self.url, {"key": str(uuid.uuid4())})
        self.assertEqual(http.HTTPStatus.NOT_FOUND, response.status_code)
        self.assertEqual({"error": "Key not found."}, response.json())

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
