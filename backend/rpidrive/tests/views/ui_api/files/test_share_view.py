import http
import os
import uuid

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import resolve

from rpidrive.controllers.local_file import create_entry
from rpidrive.controllers.volume import VolumePermissionModel, update_volume_permission
from rpidrive.models import PublicFileLink, VolumePermissionEnum
from rpidrive.tests.helpers.setup import SetupContext
from rpidrive.views.ui_api.files import FileShareView


class TestFileShareView(TestCase):
    """Test FileShareView"""

    def setUp(self):
        self.context = SetupContext()
        self.url = f"/drive/ui-api/files/{uuid.uuid4()}/share"
        self.user = User.objects.create_user("z")

    def tearDown(self):
        self.context.cleanup()
        User.objects.all().delete()

    def test_url(self):
        """Test url"""
        self.assertEqual(FileShareView, resolve(self.url).func.view_class)

    def test_post_1(self):
        """Test POST method"""
        f_p = os.path.join(self.context.root_path, "music.m4a")
        with open(f_p, "w+") as f_h:
            f_h.write("a")
        file_obj = create_entry(self.context.volume, self.context.root_file, f_p)
        file_url = f"/drive/ui-api/files/{file_obj.id}/share"

        self.client.force_login(self.context.admin)
        response = self.client.post(file_url)
        link = PublicFileLink.objects.first()
        self.assertEqual(http.HTTPStatus.OK, response.status_code)
        self.assertEqual({"id": str(link.id)}, response.json())

    def test_post_2(self):
        """Test POST method (Invalid id)"""
        self.client.force_login(self.context.admin)
        response = self.client.post(self.url)
        self.assertEqual(http.HTTPStatus.NOT_FOUND, response.status_code)
        self.assertEqual({"error": "File not found."}, response.json())

    def test_post_3(self):
        """Test POST method (Non-admin user)"""
        f_p = os.path.join(self.context.root_path, "music.m4a")
        with open(f_p, "w+") as f_h:
            f_h.write("a")
        file_obj = create_entry(self.context.volume, self.context.root_file, f_p)
        file_url = f"/drive/ui-api/files/{file_obj.id}/share"

        self.client.force_login(self.user)
        response = self.client.post(file_url)
        self.assertEqual(http.HTTPStatus.NOT_FOUND, response.status_code)
        self.assertEqual({"error": "File not found."}, response.json())
        self.assertFalse(PublicFileLink.objects.exists())

        update_volume_permission(
            self.context.admin,
            self.context.volume.id,
            [
                VolumePermissionModel(
                    user=self.user.id, permission=VolumePermissionEnum.READ
                )
            ],
        )
        response = self.client.post(file_url)
        link = PublicFileLink.objects.first()
        self.assertEqual(http.HTTPStatus.OK, response.status_code)
        self.assertEqual({"id": str(link.id)}, response.json())

    def test_post_4(self):
        """Test POST method (No login)"""
        response = self.client.post(self.url)
        self.assertEqual(http.HTTPStatus.FOUND, response.status_code)
        self.assertEqual(b"", response.content)

    def test_get_1(self):
        """Test GET method"""
        self.client.force_login(self.context.admin)
        response = self.client.get(self.url)
        self.assertEqual(http.HTTPStatus.METHOD_NOT_ALLOWED, response.status_code)
        self.assertEqual(b"", response.content)

    def test_get_2(self):
        """Test GET method (No login)"""
        response = self.client.get(self.url)
        self.assertEqual(http.HTTPStatus.FOUND, response.status_code)
        self.assertEqual(b"", response.content)

    def test_put_1(self):
        """Test PUT method"""
        self.client.force_login(self.context.admin)
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
        self.client.force_login(self.context.admin)
        response = self.client.delete(self.url)
        self.assertEqual(http.HTTPStatus.METHOD_NOT_ALLOWED, response.status_code)
        self.assertEqual(b"", response.content)

    def test_delete_2(self):
        """Test DELETE method (No login)"""
        response = self.client.delete(self.url)
        self.assertEqual(http.HTTPStatus.FOUND, response.status_code)
        self.assertEqual(b"", response.content)
