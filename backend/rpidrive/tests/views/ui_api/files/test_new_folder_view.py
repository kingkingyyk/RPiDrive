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
from rpidrive.views.ui_api.files import NewFolderView


class TestNewFolderView(TestCase):
    """Test new folder view"""

    def setUp(self):
        self.context = SetupContext()
        self.url = f"/drive/ui-api/files/{self.context.root_file.id}/new-folder"
        self.user = User.objects.create_user("z")

    def tearDown(self):
        self.context.cleanup()
        User.objects.all().delete()

    def test_url(self):
        """Test url"""
        self.assertEqual(NewFolderView, resolve(self.url).func.view_class)

    def test_post_1(self):
        """Test POST method"""
        post_data = {"name": "example"}
        self.client.force_login(self.context.admin)
        response = self.client.post(self.url, post_data, "application/json")
        self.assertEqual(http.HTTPStatus.CREATED, response.status_code)
        self.assertEqual(2, File.objects.count())

        new_folder_id = response.json()["id"]
        self.assertEqual({"id": new_folder_id}, response.json())
        new_folder = File.objects.get(id=new_folder_id)
        self.assertEqual("example", new_folder.name)
        self.assertTrue(os.path.exists(os.path.join(self.context.root_path, "example")))
        self.assertEqual("/example", new_folder.path_from_vol)

    def test_post_2(self):
        """Test POST method (Non-admin)"""
        post_data = {"name": "example"}
        self.client.force_login(self.user)
        response = self.client.post(self.url, post_data, "application/json")
        self.assertEqual(http.HTTPStatus.NOT_FOUND, response.status_code)
        self.assertEqual({"error": "File not found."}, response.json())
        self.assertEqual(1, File.objects.count())

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
        response = self.client.post(self.url, post_data, "application/json")
        self.assertEqual(http.HTTPStatus.FORBIDDEN, response.status_code)
        self.assertEqual({"error": "No permission."}, response.json())
        self.assertEqual(1, File.objects.count())

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
        self.assertEqual(http.HTTPStatus.CREATED, response.status_code)
        self.assertEqual(2, File.objects.count())

        new_folder_id = response.json()["id"]
        self.assertEqual({"id": new_folder_id}, response.json())
        new_folder = File.objects.get(id=new_folder_id)
        self.assertEqual("example", new_folder.name)
        self.assertTrue(os.path.exists(os.path.join(self.context.root_path, "example")))
        self.assertEqual("/example", new_folder.path_from_vol)

    def test_post_3(self):
        """Test POST method (Auto strip name)"""
        post_data = {"name": "  example  "}
        self.client.force_login(self.context.admin)
        response = self.client.post(self.url, post_data, "application/json")
        self.assertEqual(http.HTTPStatus.CREATED, response.status_code)
        self.assertEqual(2, File.objects.count())

        new_folder_id = response.json()["id"]
        self.assertEqual({"id": new_folder_id}, response.json())
        new_folder = File.objects.get(id=new_folder_id)
        self.assertEqual("example", new_folder.name)
        self.assertTrue(os.path.exists(os.path.join(self.context.root_path, "example")))
        self.assertEqual("/example", new_folder.path_from_vol)

    def test_post_4(self):
        """Test POST method (Invalid destination)"""
        post_data = {"name": "example"}
        temp_url = f"/drive/ui-api/files/{uuid.uuid4()}/new-folder"
        self.client.force_login(self.context.admin)
        response = self.client.post(temp_url, post_data, "application/json")
        self.assertEqual(http.HTTPStatus.NOT_FOUND, response.status_code)
        self.assertEqual({"error": "File not found."}, response.json())
        self.assertEqual(1, File.objects.count())

    def test_post_5(self):
        """Test POST method (Invalid name)"""
        post_data = {"name": "  "}
        self.client.force_login(self.context.admin)
        response = self.client.post(self.url, post_data, "application/json")
        self.assertEqual(http.HTTPStatus.BAD_REQUEST, response.status_code)
        self.assertEqual({"error": "Folder name can't be empty."}, response.json())
        self.assertEqual(1, File.objects.count())

    def test_post_6(self):
        """Test POST method (Destination is file)"""
        fp_1 = os.path.join(self.context.root_path, "song1.m4a")
        with open(fp_1, "w+") as f_h:
            f_h.write("a")
        file_1_obj = create_entry(self.context.volume, self.context.root_file, fp_1)

        temp_url = f"/drive/ui-api/files/{file_1_obj.id}/new-folder"
        post_data = {"name": "example"}

        self.client.force_login(self.context.admin)
        response = self.client.post(temp_url, post_data, "application/json")
        self.assertEqual(http.HTTPStatus.BAD_REQUEST, response.status_code)
        self.assertEqual({"error": "Can't create folder in file."}, response.json())
        self.assertEqual(2, File.objects.count())

    def test_post_7(self):
        """Test POST method (Filename exists)"""
        fp_1 = os.path.join(self.context.root_path, "song1.m4a")
        with open(fp_1, "w+") as f_h:
            f_h.write("a")
        create_entry(self.context.volume, self.context.root_file, fp_1)

        post_data = {"name": "song1.m4a"}

        self.client.force_login(self.context.admin)
        response = self.client.post(self.url, post_data, "application/json")
        self.assertEqual(http.HTTPStatus.BAD_REQUEST, response.status_code)
        self.assertEqual({"error": "Folder name is already in use."}, response.json())
        self.assertEqual(2, File.objects.count())

    def test_post_8(self):
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