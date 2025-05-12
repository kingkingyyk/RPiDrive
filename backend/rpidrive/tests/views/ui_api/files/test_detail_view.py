import http
import os
import uuid

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import resolve

from rpidrive.controllers.local_file import create_entry
from rpidrive.controllers.volume import VolumePermissionModel, update_volume_permission
from rpidrive.models import File, VolumePermissionEnum
from rpidrive.tests.helpers.setup import SetupContext
from rpidrive.views.ui_api.files import FileDetailView


class TestFileDetailView(TestCase):
    """Test FileDetailView"""

    def setUp(self):
        self.base_url = "/drive/ui-api/files/"
        self.url = f"/drive/ui-api/files/{uuid.uuid4()}"
        self.context = SetupContext()
        self.user = User.objects.create_user("z")

    def tearDown(self):
        self.context.cleanup()
        User.objects.all().delete()

    def test_url(self):
        """Test url"""
        self.assertEqual(FileDetailView, resolve(self.url).func.view_class)

    def test_get_1(self):
        """Test GET method"""
        fp_1 = os.path.join(self.context.root_path, "song1.m4a")
        with open(fp_1, "w+") as f_h:
            f_h.write("a")
        file_1_obj = create_entry(self.context.volume, self.context.root_file, fp_1)

        file_url = f"{self.base_url}{file_1_obj.id}"
        self.client.force_login(self.context.admin)

        # Naive
        response = self.client.get(file_url)
        self.assertEqual(http.HTTPStatus.OK, response.status_code)
        data = response.json()
        self.assertEqual(str(file_1_obj.id), data["id"])
        self.assertEqual("song1.m4a", data["name"])
        self.assertEqual("file", data["kind"])
        self.assertIsNotNone(data["last_modified"])
        self.assertEqual(1, data["size"])
        self.assertIsNotNone(data["metadata"])
        self.assertEqual(str(self.context.root_file.id), data["parent_id"])
        self.assertEqual("audio/mp4", data["media_type"])

        # With volume, parent, path
        response = self.client.get(file_url, {"fields": "volume,parent,path"})
        self.assertEqual(http.HTTPStatus.OK, response.status_code)
        data = response.json()
        self.assertIsNotNone(data["volume"])
        self.assertEqual(
            {"id": str(self.context.volume.id), "name": self.context.volume.name},
            data["volume"],
        )
        self.assertIsNotNone(data["path"])
        self.assertEqual(
            [{"id": str(self.context.root_file.id), "name": ""}], data["path"]
        )

        # With children & path
        response = self.client.get(
            f"{self.base_url}{self.context.root_file.id}",
            {"fields": "children,path"},
        )
        self.assertEqual(http.HTTPStatus.OK, response.status_code)
        data = response.json()
        self.assertIsNotNone(data["path"])
        self.assertEqual([], data["path"])
        self.assertIsNotNone(data["children"])
        self.assertEqual(1, len(data["children"]))
        child_file = data["children"][0]
        self.assertTrue("metadata" in child_file)
        del child_file["metadata"]
        self.assertIsNotNone(child_file["last_modified"])
        del child_file["last_modified"]
        self.assertEqual(
            {
                "id": str(file_1_obj.id),
                "name": "song1.m4a",
                "kind": "file",
                "size": 1,
                "parent_id": str(self.context.root_file.id),
                "media_type": "audio/mp4",
            },
            child_file,
        )

    def test_get_2(self):
        """Test GET method (Non-admin)"""
        fp_1 = os.path.join(self.context.root_path, "song1.m4a")
        with open(fp_1, "w+") as f_h:
            f_h.write("a")
        file_1_obj = create_entry(self.context.volume, self.context.root_file, fp_1)

        file_url = f"{self.base_url}{file_1_obj.id}"
        self.client.force_login(self.user)
        response = self.client.get(file_url)
        self.assertEqual(http.HTTPStatus.NOT_FOUND, response.status_code)
        self.assertEqual({"error": "File not found."}, response.json())

        update_volume_permission(
            self.context.admin,
            self.context.volume.id,
            [
                VolumePermissionModel(
                    user=self.user.id, permission=VolumePermissionEnum.READ
                )
            ],
        )
        response = self.client.get(file_url)
        self.assertEqual(http.HTTPStatus.OK, response.status_code)
        data = response.json()
        del data["last_modified"]
        del data["metadata"]
        self.assertEqual(
            {
                "id": str(file_1_obj.id),
                "name": "song1.m4a",
                "kind": "file",
                "size": 1,
                "parent_id": str(self.context.root_file.id),
                "media_type": "audio/mp4",
            },
            data,
        )

    def test_get_3(self):
        """Test GET method (No login)"""
        response = self.client.get(self.url)
        self.assertEqual(http.HTTPStatus.FOUND, response.status_code)
        self.assertEqual(b"", response.content)

    def test_delete_1(self):
        """Test DELETE method"""
        fp_1 = os.path.join(self.context.root_path, "song1.m4a")
        with open(fp_1, "w+") as f_h:
            f_h.write("a")
        file_1_obj = create_entry(self.context.volume, self.context.root_file, fp_1)

        file_url = f"{self.base_url}{file_1_obj.id}"
        self.client.force_login(self.context.admin)
        response = self.client.delete(file_url)
        self.assertEqual(http.HTTPStatus.OK, response.status_code)
        self.assertEqual({}, response.json())
        self.assertFalse(os.path.exists(fp_1))
        self.assertEqual(1, File.objects.count())

    def test_delete_2(self):
        """Test DELETE method (Non-admin user)"""
        fp_1 = os.path.join(self.context.root_path, "song1.m4a")
        with open(fp_1, "w+") as f_h:
            f_h.write("a")
        file_1_obj = create_entry(self.context.volume, self.context.root_file, fp_1)

        file_url = f"{self.base_url}{file_1_obj.id}"
        self.client.force_login(self.user)
        response = self.client.delete(file_url)
        self.assertEqual(http.HTTPStatus.NOT_FOUND, response.status_code)
        self.assertEqual({"error": "Volume not found."}, response.json())
        self.assertTrue(os.path.exists(fp_1))
        self.assertEqual(2, File.objects.count())

        # Read only
        update_volume_permission(
            self.context.admin,
            self.context.volume.id,
            [
                VolumePermissionModel(
                    user=self.user.id, permission=VolumePermissionEnum.READ
                )
            ],
        )
        response = self.client.delete(file_url)
        self.assertEqual(http.HTTPStatus.FORBIDDEN, response.status_code)
        self.assertEqual({"error": "No permission."}, response.json())
        self.assertTrue(os.path.exists(fp_1))
        self.assertEqual(2, File.objects.count())

        # Read-write
        update_volume_permission(
            self.context.admin,
            self.context.volume.id,
            [
                VolumePermissionModel(
                    user=self.user.id, permission=VolumePermissionEnum.READ_WRITE
                )
            ],
        )
        response = self.client.delete(file_url)
        self.assertEqual(http.HTTPStatus.OK, response.status_code)
        self.assertEqual({}, response.json())
        self.assertFalse(os.path.exists(fp_1))
        self.assertEqual(1, File.objects.count())

    def test_delete_3(self):
        """Test DELETE method (Invalid file id)"""
        self.client.force_login(self.context.admin)
        response = self.client.delete(self.url)
        self.assertEqual(http.HTTPStatus.NOT_FOUND, response.status_code)
        self.assertEqual({"error": "File not found."}, response.json())

    def test_delete_4(self):
        """Test DELETE method (Root file)"""
        file_url = f"{self.base_url}{self.context.root_file.id}"
        self.client.force_login(self.context.admin)
        response = self.client.delete(file_url)
        self.assertEqual(http.HTTPStatus.BAD_REQUEST, response.status_code)
        self.assertEqual({"error": "Can't delete root file."}, response.json())

    def test_delete_5(self):
        """Test DELETE method (No login)"""
        response = self.client.delete(self.url)
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

    def test_post_1(self):
        """Test POST method"""
        self.client.force_login(self.context.admin)
        response = self.client.post(self.url)
        self.assertEqual(http.HTTPStatus.METHOD_NOT_ALLOWED, response.status_code)
        self.assertEqual(b"", response.content)

    def test_post_2(self):
        """Test POST method"""
        response = self.client.post(self.url)
        self.assertEqual(http.HTTPStatus.FOUND, response.status_code)
        self.assertEqual(b"", response.content)
