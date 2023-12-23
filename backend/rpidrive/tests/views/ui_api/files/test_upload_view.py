import http
import os
import uuid

from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import resolve

from rpidrive.controllers.local_file import create_entry
from rpidrive.controllers.volume import VolumePermissionModel, update_volume_permission
from rpidrive.models import File, VolumePermissionEnum
from rpidrive.tests.helpers.setup import SetupContext
from rpidrive.views.ui_api.files import FileUploadView


class TestFileUploadView(TestCase):
    """Test FileUploadView"""

    @staticmethod
    def _get_url(file_id: str) -> str:
        return f"/drive/ui-api/files/{file_id}/upload"

    def setUp(self):
        self.context = SetupContext()
        self.url = self._get_url(self.context.root_file.id)
        self.user = User.objects.create_user("z")
        self.curr_path = os.path.dirname(os.path.realpath(__file__))

    def tearDown(self):
        self.context.cleanup()
        User.objects.all().delete()

    def test_url(self):
        """Test url"""
        self.assertEqual(FileUploadView, resolve(self.url).func.view_class)

    def test_post_1(self):
        """Test POST method"""
        sample_file = os.path.join(self.curr_path, "sample.m4a")
        self.client.force_login(self.context.admin)

        with open(sample_file, "rb") as f_h:
            ul_file = SimpleUploadedFile("sample.m4a", f_h.read())
            response = self.client.post(
                self._get_url(self.context.root_file.id),
                {"files": ul_file, "paths": ["lel/sample.m4a"]},
            )

        self.assertEqual(http.HTTPStatus.CREATED, response.status_code)
        self.assertEqual({}, response.json())
        self.assertEqual(3, File.objects.count())
        self.assertTrue(os.path.join(self.context.root_path, "lel", "sample.m4a"))

        lel_folder = File.objects.get(name="lel")
        self.assertEqual("/lel", lel_folder.path_from_vol)
        self.assertEqual("folder", lel_folder.kind)
        self.assertEqual(self.context.root_file, lel_folder.parent)
        self.assertEqual(self.context.volume, lel_folder.volume)

        sample_file = File.objects.get(name="sample.m4a")
        self.assertEqual("/lel/sample.m4a", sample_file.path_from_vol)
        self.assertEqual("file", sample_file.kind)
        self.assertEqual(lel_folder, sample_file.parent)
        self.assertEqual(self.context.volume, sample_file.volume)
        self.assertEqual("audio/mp4", sample_file.media_type)
        self.assertIsNotNone(sample_file.last_modified)
        self.assertEqual(260492, sample_file.size)
        self.assertIsNotNone(sample_file.metadata)
        self.assertEqual("anya", sample_file.metadata["album"])

    def test_post_2(self):
        """Test POST method (Duplicate name)"""
        folder_path = os.path.join(self.context.root_path, "example")
        os.makedirs(folder_path)
        folder_obj = create_entry(
            self.context.volume, self.context.root_file, folder_path
        )

        f_p = os.path.join(folder_path, "sample.m4a")
        with open(f_p, "w+") as f_h:
            f_h.write("a")
        create_entry(self.context.volume, folder_obj, f_p)

        sample_file = os.path.join(self.curr_path, "sample.m4a")
        self.client.force_login(self.context.admin)

        with open(sample_file, "rb") as f_h:
            ul_file = SimpleUploadedFile("sample.m4a", f_h.read())
            response = self.client.post(
                self._get_url(self.context.root_file.id),
                {"files": ul_file, "paths": ["example/sample.m4a"]},
            )

        self.assertEqual(http.HTTPStatus.CREATED, response.status_code)
        self.assertEqual({}, response.json())
        self.assertEqual(4, File.objects.count())

        old_sample_file = File.objects.get(name="sample.m4a")
        self.assertEqual("/example/sample.m4a", old_sample_file.path_from_vol)
        self.assertTrue(os.path.join(self.context.root_path, "example", "sample.m4a"))
        new_sample_file = File.objects.get(name="sample (1).m4a")
        self.assertEqual("/example/sample (1).m4a", new_sample_file.path_from_vol)
        self.assertTrue(
            os.path.join(self.context.root_path, "example", "sample (1).m4a")
        )

    def test_post_3(self):
        """Test POST method (Non-admin user)"""
        sample_file = os.path.join(self.curr_path, "sample.m4a")
        self.client.force_login(self.user)

        with open(sample_file, "rb") as f_h:
            ul_file = SimpleUploadedFile("sample.m4a", f_h.read())
            response = self.client.post(
                self._get_url(self.context.root_file.id),
                {"files": ul_file, "paths": ["sample.m4a"]},
            )
        self.assertEqual(http.HTTPStatus.NOT_FOUND, response.status_code)
        self.assertEqual({"error": "File not found."}, response.json())
        self.assertEqual(1, File.objects.count())

        update_volume_permission(
            self.context.admin,
            self.context.volume.id,
            [
                VolumePermissionModel(
                    user=self.user.id, permission=VolumePermissionEnum.READ
                )
            ],
        )
        with open(sample_file, "rb") as f_h:
            ul_file = SimpleUploadedFile("sample.m4a", f_h.read())
            response = self.client.post(
                self._get_url(self.context.root_file.id),
                {"files": ul_file, "paths": ["sample.m4a"]},
            )
        self.assertEqual(http.HTTPStatus.FORBIDDEN, response.status_code)
        self.assertEqual({"error": "No permission."}, response.json())
        self.assertEqual(1, File.objects.count())

        update_volume_permission(
            self.context.admin,
            self.context.volume.id,
            [
                VolumePermissionModel(
                    user=self.user.id, permission=VolumePermissionEnum.READ_WRITE
                )
            ],
        )
        with open(sample_file, "rb") as f_h:
            ul_file = SimpleUploadedFile("sample.m4a", f_h.read())
            response = self.client.post(
                self._get_url(self.context.root_file.id),
                {"files": ul_file, "paths": ["sample.m4a"]},
            )
        self.assertEqual(http.HTTPStatus.CREATED, response.status_code)
        self.assertEqual({}, response.json())
        self.assertEqual(2, File.objects.count())
        new_file = File.objects.get(name="sample.m4a")
        self.assertEqual("/sample.m4a", new_file.path_from_vol)

    def test_post_4(self):
        """Test POST method (Invalid destination id)"""
        temp_url = self._get_url(uuid.uuid4())
        sample_file = os.path.join(self.curr_path, "sample.m4a")
        self.client.force_login(self.context.admin)
        with open(sample_file, "rb") as f_h:
            ul_file = SimpleUploadedFile("sample.m4a", f_h.read())
            response = self.client.post(
                temp_url,
                {"files": ul_file, "paths": [""]},
            )
        self.assertEqual(http.HTTPStatus.NOT_FOUND, response.status_code)
        self.assertEqual({"error": "File not found."}, response.json())

    def test_post_5(self):
        """Test POST method (Empty file list)"""
        self.client.force_login(self.context.admin)
        response = self.client.post(self.url, {"files": [], "paths": []})
        self.assertEqual(http.HTTPStatus.BAD_REQUEST, response.status_code)
        self.assertEqual({"error": "No file was uploaded."}, response.json())

    def test_post_6(self):
        """Test POST method (Destination is file)"""
        f_p = os.path.join(self.context.root_path, "dummy2.m4a")
        with open(f_p, "w+") as f_h:
            f_h.write("a")
        file_obj = create_entry(self.context.volume, self.context.root_file, f_p)

        sample_file = os.path.join(self.curr_path, "sample.m4a")
        self.client.force_login(self.context.admin)
        with open(sample_file, "rb") as f_h:
            ul_file = SimpleUploadedFile("sample.m4a", f_h.read())
            response = self.client.post(
                self._get_url(file_obj.id),
                {"files": ul_file, "paths": [""]},
            )
        self.assertEqual(http.HTTPStatus.BAD_REQUEST, response.status_code)
        self.assertEqual({"error": "Unable to upload files to file."}, response.json())

    def test_post_7(self):
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
