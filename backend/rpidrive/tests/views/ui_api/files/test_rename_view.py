import http
import os
import uuid

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import resolve

from rpidrive.controllers.local_file import create_entry
from rpidrive.controllers.volume import VolumePermissionModel, update_volume_permission
from rpidrive.models import VolumePermissionEnum
from rpidrive.tests.helpers.setup import SetupContext
from rpidrive.views.ui_api.files import FileRenameView


class TestRenameView(TestCase):
    """Test rename view"""

    def setUp(self):
        self.context = SetupContext()
        self.url = f"/drive/ui-api/files/{self.context.root_file.id}/rename"
        self.user = User.objects.create_user("z")

    def tearDown(self):
        self.context.cleanup()
        User.objects.all().delete()

    def test_url(self):
        """Test url"""
        self.assertEqual(FileRenameView, resolve(self.url).func.view_class)

    def test_post_1(self):
        """Test POST method"""
        folder_path = os.path.join(self.context.root_path, "example")
        os.makedirs(folder_path)
        folder_obj = create_entry(
            self.context.volume, self.context.root_file, folder_path
        )
        folder_url = f"/drive/ui-api/files/{folder_obj.id}/rename"

        fp_1 = os.path.join(folder_path, "song.m4a")
        with open(fp_1, "w+") as f_h:
            f_h.write("a")
        file_1_obj = create_entry(self.context.volume, folder_obj, fp_1)

        post_data = {"name": "XD"}
        self.client.force_login(self.context.admin)
        response = self.client.post(folder_url, post_data, "application/json")
        self.assertEqual(http.HTTPStatus.OK, response.status_code)
        self.assertEqual({}, response.json())

        folder_obj.refresh_from_db()
        file_1_obj.refresh_from_db()
        self.assertTrue(os.path.exists(os.path.join(self.context.root_path, "XD")))
        self.assertEqual("XD", folder_obj.name)
        self.assertEqual("/XD", folder_obj.path_from_vol)
        self.assertTrue(
            os.path.exists(os.path.join(self.context.root_path, "XD", "song.m4a"))
        )
        self.assertEqual("song.m4a", file_1_obj.name)
        self.assertEqual("/XD/song.m4a", file_1_obj.path_from_vol)

    def test_post_2(self):
        """Test POST method (Auto strip name)"""
        folder_path = os.path.join(self.context.root_path, "example")
        os.makedirs(folder_path)
        folder_obj = create_entry(
            self.context.volume, self.context.root_file, folder_path
        )
        folder_url = f"/drive/ui-api/files/{folder_obj.id}/rename"

        post_data = {"name": " aa "}
        self.client.force_login(self.context.admin)
        response = self.client.post(folder_url, post_data, "application/json")
        self.assertEqual(http.HTTPStatus.OK, response.status_code)
        self.assertEqual({}, response.json())

        folder_obj.refresh_from_db()
        self.assertTrue(os.path.exists(os.path.join(self.context.root_path, "aa")))
        self.assertEqual("aa", folder_obj.name)
        self.assertEqual("/aa", folder_obj.path_from_vol)

    def test_post_3(self):
        """Test POST method (Non-admin user)"""
        folder_path = os.path.join(self.context.root_path, "example")
        os.makedirs(folder_path)
        folder_obj = create_entry(
            self.context.volume, self.context.root_file, folder_path
        )
        folder_url = f"/drive/ui-api/files/{folder_obj.id}/rename"

        post_data = {"name": "aa"}
        self.client.force_login(self.user)

        response = self.client.post(folder_url, post_data, "application/json")
        self.assertEqual(http.HTTPStatus.NOT_FOUND, response.status_code)
        self.assertEqual({"error": "File not found."}, response.json())
        folder_obj.refresh_from_db()
        self.assertTrue(os.path.exists(os.path.join(self.context.root_path, "example")))
        self.assertEqual("example", folder_obj.name)
        self.assertEqual("/example", folder_obj.path_from_vol)

        update_volume_permission(
            self.context.admin,
            self.context.volume.id,
            [
                VolumePermissionModel(
                    user=self.user.id, permission=VolumePermissionEnum.READ
                )
            ],
        )
        response = self.client.post(folder_url, post_data, "application/json")
        self.assertEqual(http.HTTPStatus.FORBIDDEN, response.status_code)
        self.assertEqual({"error": "No permission."}, response.json())
        folder_obj.refresh_from_db()
        self.assertTrue(os.path.exists(os.path.join(self.context.root_path, "example")))
        self.assertEqual("example", folder_obj.name)
        self.assertEqual("/example", folder_obj.path_from_vol)

        update_volume_permission(
            self.context.admin,
            self.context.volume.id,
            [
                VolumePermissionModel(
                    user=self.user.id, permission=VolumePermissionEnum.READ_WRITE
                )
            ],
        )
        response = self.client.post(folder_url, post_data, "application/json")
        self.assertEqual(http.HTTPStatus.OK, response.status_code)
        self.assertEqual({}, response.json())
        folder_obj.refresh_from_db()
        self.assertTrue(os.path.exists(os.path.join(self.context.root_path, "aa")))
        self.assertEqual("aa", folder_obj.name)
        self.assertEqual("/aa", folder_obj.path_from_vol)

    def test_post_4(self):
        """Test POST method (Invalid name)"""
        folder_path = os.path.join(self.context.root_path, "example")
        os.makedirs(folder_path)
        folder_obj = create_entry(
            self.context.volume, self.context.root_file, folder_path
        )
        folder_url = f"/drive/ui-api/files/{folder_obj.id}/rename"

        post_data = {"name": "  "}
        self.client.force_login(self.context.admin)
        response = self.client.post(folder_url, post_data, "application/json")
        self.assertEqual(http.HTTPStatus.BAD_REQUEST, response.status_code)
        self.assertEqual({"error": "Invalid file name."}, response.json())

    def test_post_5(self):
        """Test POST method (Duplicate name)"""
        folder_path = os.path.join(self.context.root_path, "example")
        os.makedirs(folder_path)
        folder_obj = create_entry(
            self.context.volume, self.context.root_file, folder_path
        )
        folder_url = f"/drive/ui-api/files/{folder_obj.id}/rename"

        folder_path_2 = os.path.join(self.context.root_path, "example2")
        os.makedirs(folder_path_2)
        create_entry(self.context.volume, self.context.root_file, folder_path_2)

        post_data = {"name": "example2"}
        self.client.force_login(self.context.admin)
        response = self.client.post(folder_url, post_data, "application/json")
        self.assertEqual(http.HTTPStatus.BAD_REQUEST, response.status_code)
        self.assertEqual({"error": "File name is already in use."}, response.json())

    def test_post_6(self):
        """Test POST method (Invalid name)"""
        folder_path = os.path.join(self.context.root_path, "example")
        os.makedirs(folder_path)
        folder_obj = create_entry(
            self.context.volume, self.context.root_file, folder_path
        )
        folder_url = f"/drive/ui-api/files/{folder_obj.id}/rename"

        post_data = {"name": "a/a"}
        self.client.force_login(self.context.admin)
        response = self.client.post(folder_url, post_data, "application/json")
        self.assertEqual(http.HTTPStatus.BAD_REQUEST, response.status_code)
        self.assertEqual({"error": "Invalid character in file name."}, response.json())

    def test_post_7(self):
        """Test POST method (Non-admin user)"""
        folder_path = os.path.join(self.context.root_path, "example")
        os.makedirs(folder_path)
        folder_obj = create_entry(
            self.context.volume, self.context.root_file, folder_path
        )
        folder_url = f"/drive/ui-api/files/{folder_obj.id}/rename"

        post_data = {"name": "XD"}
        self.client.force_login(self.user)
        response = self.client.post(folder_url, post_data, "application/json")
        self.assertEqual(http.HTTPStatus.NOT_FOUND, response.status_code)
        self.assertEqual({"error": "File not found."}, response.json())
        folder_obj.refresh_from_db()
        self.assertTrue(os.path.exists(os.path.join(self.context.root_path, "example")))
        self.assertEqual("example", folder_obj.name)
        self.assertEqual("/example", folder_obj.path_from_vol)

        update_volume_permission(
            self.context.admin,
            self.context.volume.id,
            [
                VolumePermissionModel(
                    user=self.user.id,
                    permission=VolumePermissionEnum.READ,
                )
            ],
        )
        response = self.client.post(folder_url, post_data, "application/json")
        self.assertEqual(http.HTTPStatus.FORBIDDEN, response.status_code)
        self.assertEqual({"error": "No permission."}, response.json())
        folder_obj.refresh_from_db()
        self.assertTrue(os.path.exists(os.path.join(self.context.root_path, "example")))
        self.assertEqual("example", folder_obj.name)
        self.assertEqual("/example", folder_obj.path_from_vol)

        update_volume_permission(
            self.context.admin,
            self.context.volume.id,
            [
                VolumePermissionModel(
                    user=self.user.id,
                    permission=VolumePermissionEnum.READ_WRITE,
                )
            ],
        )
        response = self.client.post(folder_url, post_data, "application/json")
        self.assertEqual(http.HTTPStatus.OK, response.status_code)
        self.assertEqual({}, response.json())
        folder_obj.refresh_from_db()
        self.assertTrue(os.path.exists(os.path.join(self.context.root_path, "XD")))
        self.assertEqual("XD", folder_obj.name)
        self.assertEqual("/XD", folder_obj.path_from_vol)

    def test_post_8(self):
        """Test POST method (Invalid file id)"""
        folder_url = f"/drive/ui-api/files/{uuid.uuid4()}/rename"

        post_data = {"name": "XD"}
        self.client.force_login(self.context.admin)
        response = self.client.post(folder_url, post_data, "application/json")
        self.assertEqual(http.HTTPStatus.NOT_FOUND, response.status_code)
        self.assertEqual({"error": "File not found."}, response.json())

    def test_post_9(self):
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
