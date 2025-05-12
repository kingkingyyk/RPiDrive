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
from rpidrive.views.ui_api.files import FileMoveView


class TestFileMoveView(TestCase):
    """Test FileMoveView"""

    def setUp(self):
        self.url = "/drive/ui-api/files/move"
        self.context = SetupContext()
        self.user = User.objects.create_user("z")

    def tearDown(self):
        self.context.cleanup()
        User.objects.all().delete()

    def test_url(self):
        """Test url"""
        self.assertEqual(FileMoveView, resolve(self.url).func.view_class)

    def test_post_1(self):
        """Test POST method"""
        fp_1 = os.path.join(self.context.root_path, "song1.m4a")
        with open(fp_1, "w+") as f_h:
            f_h.write("a")
        file_1_obj = create_entry(self.context.volume, self.context.root_file, fp_1)

        folder_path = os.path.join(self.context.root_path, "example")
        os.makedirs(folder_path)
        folder_obj = create_entry(
            self.context.volume, self.context.root_file, folder_path
        )

        fp_2 = os.path.join(folder_path, "song1.m4a")
        with open(fp_2, "w+") as f_h:
            f_h.write("a")
        create_entry(self.context.volume, folder_obj, fp_2)

        post_data = {
            "files": [str(file_1_obj.id)],
            "strategy": "rename",
            "move_to": str(folder_obj.id),
        }
        self.client.force_login(self.context.admin)
        response = self.client.post(self.url, post_data, "application/json")
        self.assertEqual(http.HTTPStatus.OK, response.status_code)
        self.assertEqual({}, response.json())

        self.assertEqual(4, File.objects.count())
        file_1_obj.refresh_from_db()
        self.assertTrue(os.path.exists(os.path.join(folder_path, "song1 (1).m4a")))
        self.assertEqual("song1 (1).m4a", file_1_obj.name)
        self.assertEqual(folder_obj, file_1_obj.parent)
        self.assertEqual("/example/song1 (1).m4a", file_1_obj.path_from_vol)

    def test_post_2(self):
        """Test POST method (Empty files)"""
        folder_path = os.path.join(self.context.root_path, "example")
        os.makedirs(folder_path)
        folder_obj = create_entry(
            self.context.volume, self.context.root_file, folder_path
        )

        post_data = {
            "files": [],
            "strategy": "rename",
            "move_to": str(folder_obj.id),
        }
        self.client.force_login(self.context.admin)
        response = self.client.post(self.url, post_data, "application/json")
        self.assertEqual(http.HTTPStatus.BAD_REQUEST, response.status_code)
        self.assertEqual({"error": "No file to move."}, response.json())

    def test_post_3(self):
        """Test POST method (Invalid strategy)"""
        fp_1 = os.path.join(self.context.root_path, "song1.m4a")
        with open(fp_1, "w+") as f_h:
            f_h.write("a")
        file_1_obj = create_entry(self.context.volume, self.context.root_file, fp_1)

        folder_path = os.path.join(self.context.root_path, "example")
        os.makedirs(folder_path)
        folder_obj = create_entry(
            self.context.volume, self.context.root_file, folder_path
        )

        post_data = {
            "files": [str(file_1_obj.id)],
            "strategy": "LOLLLL",
            "move_to": str(folder_obj.id),
        }
        self.client.force_login(self.context.admin)
        response = self.client.post(self.url, post_data, "application/json")
        self.assertEqual(http.HTTPStatus.BAD_REQUEST, response.status_code)
        self.assertEqual(
            {"error": "strategy -> Input should be 'rename' or 'overwrite'"},
            response.json(),
        )

    def test_post_4(self):
        """Test POST method (Invalid files)"""
        folder_path = os.path.join(self.context.root_path, "example")
        os.makedirs(folder_path)
        folder_obj = create_entry(
            self.context.volume, self.context.root_file, folder_path
        )

        post_data = {
            "files": [str(uuid.uuid4())],
            "strategy": "rename",
            "move_to": str(folder_obj.id),
        }
        self.client.force_login(self.context.admin)
        response = self.client.post(self.url, post_data, "application/json")
        self.assertEqual(http.HTTPStatus.BAD_REQUEST, response.status_code)
        self.assertEqual(
            {"error": "No file to move."},
            response.json(),
        )

    def test_post_5(self):
        """Test POST method (Invalid destination)"""
        fp_1 = os.path.join(self.context.root_path, "song1.m4a")
        with open(fp_1, "w+") as f_h:
            f_h.write("a")
        file_1_obj = create_entry(self.context.volume, self.context.root_file, fp_1)

        post_data = {
            "files": [str(file_1_obj.id)],
            "strategy": "rename",
            "move_to": str(uuid.uuid4()),
        }
        self.client.force_login(self.context.admin)
        response = self.client.post(self.url, post_data, "application/json")
        self.assertEqual(http.HTTPStatus.NOT_FOUND, response.status_code)
        self.assertEqual(
            {"error": "File not found."},
            response.json(),
        )
        self.assertTrue(os.path.exists(fp_1))

    def test_post_6(self):
        """Test POST method (Non-admin user)"""
        fp_1 = os.path.join(self.context.root_path, "song1.m4a")
        with open(fp_1, "w+") as f_h:
            f_h.write("a")
        file_1_obj = create_entry(self.context.volume, self.context.root_file, fp_1)

        folder_path = os.path.join(self.context.root_path, "example")
        os.makedirs(folder_path)
        folder_obj = create_entry(
            self.context.volume, self.context.root_file, folder_path
        )

        fp_2 = os.path.join(folder_path, "song1.m4a")
        with open(fp_2, "w+") as f_h:
            f_h.write("a")
        file_2_obj = create_entry(self.context.volume, folder_obj, fp_2)

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
        post_data = {
            "files": [str(file_1_obj.id)],
            "strategy": "overwrite",
            "move_to": str(folder_obj.id),
        }
        self.client.force_login(self.user)
        response = self.client.post(self.url, post_data, "application/json")
        self.assertEqual(http.HTTPStatus.FORBIDDEN, response.status_code)
        self.assertEqual({"error": "No permission."}, response.json())
        self.assertEqual(4, File.objects.count())

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

        response = self.client.post(self.url, post_data, "application/json")
        self.assertEqual(http.HTTPStatus.OK, response.status_code)
        self.assertEqual({}, response.json())

        self.assertEqual(3, File.objects.count())
        self.assertFalse(File.objects.filter(id=file_2_obj.id).exists())
        file_1_obj.refresh_from_db()
        self.assertTrue(os.path.exists(os.path.join(folder_path, "song1.m4a")))
        self.assertEqual("song1.m4a", file_1_obj.name)
        self.assertEqual(folder_obj, file_1_obj.parent)
        self.assertEqual("/example/song1.m4a", file_1_obj.path_from_vol)

    def test_post_7(self):
        """Test POST method (No login)"""
        response = self.client.post(self.url)
        self.assertEqual(http.HTTPStatus.FOUND, response.status_code)
        self.assertEqual(b"", response.content)

    def test_get_1(self):
        """Test PUT method"""
        self.client.force_login(self.context.admin)
        response = self.client.get(self.url)
        self.assertEqual(http.HTTPStatus.METHOD_NOT_ALLOWED, response.status_code)
        self.assertEqual(b"", response.content)

    def test_get_2(self):
        """Test PUT method (No login)"""
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
