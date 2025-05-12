import http
import os
import uuid

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import resolve

from rpidrive.controllers.local_file import create_entry
from rpidrive.controllers.playlists import (
    add_playlist_file,
    create_playlist,
)
from rpidrive.controllers.volume import VolumePermissionModel, update_volume_permission
from rpidrive.models import Playlist, PlaylistFile, VolumePermissionEnum
from rpidrive.tests.helpers.setup import SetupContext
from rpidrive.views.ui_api.playlists import PlaylistDetailView


class TestPlaylistDetailView(TestCase):
    """Test playlist detail view"""

    def setUp(self):
        self.base_url = "/drive/ui-api/playlists/"
        self.url = f"{self.base_url}{uuid.uuid4()}"
        self.context = SetupContext()
        self.user = User.objects.create_user("z")

    def tearDown(self):
        self.context.cleanup()
        User.objects.all().delete()

    def test_url(self):
        """Test url"""
        self.assertEqual(PlaylistDetailView, resolve(self.url).func.view_class)

    def test_get_1(self):
        """Test GET method"""
        fp_1 = os.path.join(self.context.root_path, "song1.m4a")
        with open(fp_1, "w+") as f_h:
            f_h.write("a")
        file_1_obj = create_entry(self.context.volume, self.context.root_file, fp_1)

        fp_2 = os.path.join(self.context.root_path, "song2.m4a")
        with open(fp_2, "w+") as f_h:
            f_h.write("a")
        file_2_obj = create_entry(self.context.volume, self.context.root_file, fp_2)

        update_volume_permission(
            self.context.admin,
            str(self.context.volume.id),
            [
                VolumePermissionModel(
                    user=self.user.pk,
                    permission=VolumePermissionEnum.READ_WRITE,
                )
            ],
        )

        playlist = create_playlist(self.user, "LOL")
        add_playlist_file(self.user, playlist.id, file_2_obj.id)
        add_playlist_file(self.user, playlist.id, file_1_obj.id)

        self.client.force_login(self.user)
        response = self.client.get(f"{self.base_url}{playlist.id}")
        self.assertEqual(http.HTTPStatus.OK, response.status_code)

        data = response.json()
        self.assertEqual(str(playlist.id), data["id"])
        self.assertEqual(playlist.name, data["name"])
        self.assertEqual(2, len(data["files"]))
        self.assertEqual(str(file_2_obj.id), data["files"][0]["source_id"])
        self.assertEqual(file_2_obj.name, data["files"][0]["name"])
        self.assertIsNotNone(data["files"][0]["metadata"])
        self.assertEqual(str(file_1_obj.id), data["files"][1]["source_id"])
        self.assertEqual(file_1_obj.name, data["files"][1]["name"])
        self.assertIsNotNone(data["files"][1]["metadata"])

    def test_get_2(self):
        """Test GET method (Other user's playlist)"""
        playlist = create_playlist(self.context.admin, "LOL")
        self.client.force_login(self.user)
        response = self.client.get(f"{self.base_url}{playlist.id}")
        self.assertEqual(http.HTTPStatus.NOT_FOUND, response.status_code)
        self.assertEqual({"error": "Playlist not found."}, response.json())

    def test_get_3(self):
        """Test GET method (No login)"""
        response = self.client.get(self.url)
        self.assertEqual(http.HTTPStatus.FOUND, response.status_code)
        self.assertEqual(b"", response.content)

    def test_post_1(self):
        """Test POST method (Rename)"""
        post_data = {
            "action": "rename",
            "name": " GG",
        }
        playlist = create_playlist(self.user, "LOL")
        self.client.force_login(self.user)
        response = self.client.post(
            f"{self.base_url}{playlist.id}", post_data, "application/json"
        )
        self.assertEqual(http.HTTPStatus.OK, response.status_code)
        self.assertEqual({"id": str(playlist.id), "name": "GG"}, response.json())
        playlist.refresh_from_db()
        self.assertEqual("GG", playlist.name)

    def test_post_2(self):
        """Test POST method (Not owner)"""
        post_data = {
            "action": "rename",
            "name": " GG",
        }
        playlist = create_playlist(self.user, "LOL")
        self.client.force_login(self.context.admin)
        response = self.client.post(
            f"{self.base_url}{playlist.id}", post_data, "application/json"
        )
        self.assertEqual(http.HTTPStatus.NOT_FOUND, response.status_code)
        self.assertEqual({"error": "Playlist not found."}, response.json())
        playlist.refresh_from_db()
        self.assertEqual("LOL", playlist.name)

    def test_post_3(self):
        """Test POST method (Add file)"""
        fp_1 = os.path.join(self.context.root_path, "song1.m4a")
        with open(fp_1, "w+") as f_h:
            f_h.write("a")
        file_1_obj = create_entry(self.context.volume, self.context.root_file, fp_1)

        fp_2 = os.path.join(self.context.root_path, "song2.m4a")
        with open(fp_2, "w+") as f_h:
            f_h.write("a")
        file_2_obj = create_entry(self.context.volume, self.context.root_file, fp_2)

        # Add first file
        post_data = {
            "action": "add-file",
            "file_id": str(file_1_obj.id),
        }
        playlist = create_playlist(self.context.admin, "LOL")
        self.client.force_login(self.context.admin)
        response = self.client.post(
            f"{self.base_url}{playlist.id}", post_data, "application/json"
        )
        self.assertEqual(http.HTTPStatus.OK, response.status_code)
        self.assertEqual({"id": str(playlist.id), "name": "LOL"}, response.json())

        self.assertEqual(1, PlaylistFile.objects.count())
        pl_file = PlaylistFile.objects.first()
        self.assertEqual(file_1_obj, pl_file.file)
        self.assertEqual(playlist, pl_file.playlist)
        self.assertEqual(0, pl_file.sequence)

        # Add second file
        post_data = {
            "action": "add-file",
            "file_id": str(file_2_obj.id),
        }
        response = self.client.post(
            f"{self.base_url}{playlist.id}", post_data, "application/json"
        )
        self.assertEqual(http.HTTPStatus.OK, response.status_code)
        self.assertEqual({"id": str(playlist.id), "name": "LOL"}, response.json())

        self.assertEqual(2, PlaylistFile.objects.count())
        pl_file = PlaylistFile.objects.last()
        self.assertEqual(file_2_obj, pl_file.file)
        self.assertEqual(playlist, pl_file.playlist)
        self.assertEqual(1, pl_file.sequence)

    def test_post_4(self):
        """Test POST method (Remove file)"""
        fp_1 = os.path.join(self.context.root_path, "song1.m4a")
        with open(fp_1, "w+") as f_h:
            f_h.write("a")
        file_1_obj = create_entry(self.context.volume, self.context.root_file, fp_1)

        fp_2 = os.path.join(self.context.root_path, "song2.m4a")
        with open(fp_2, "w+") as f_h:
            f_h.write("a")
        file_2_obj = create_entry(self.context.volume, self.context.root_file, fp_2)

        playlist = create_playlist(self.context.admin, "LOL")
        add_playlist_file(self.context.admin, playlist.id, file_1_obj.id)
        add_playlist_file(self.context.admin, playlist.id, file_2_obj.id)

        # Remove first file
        post_data = {
            "action": "remove-file",
            "file_id": PlaylistFile.objects.get(file=file_1_obj).id,
        }
        self.client.force_login(self.context.admin)
        response = self.client.post(
            f"{self.base_url}{playlist.id}", post_data, "application/json"
        )
        self.assertEqual(http.HTTPStatus.OK, response.status_code)
        self.assertEqual({"id": str(playlist.id), "name": "LOL"}, response.json())

        self.assertEqual(1, PlaylistFile.objects.filter(file=file_2_obj).count())

    def test_post_5(self):
        """Test POST method (Remove file)"""
        fp_1 = os.path.join(self.context.root_path, "song1.m4a")
        with open(fp_1, "w+") as f_h:
            f_h.write("a")
        file_1_obj = create_entry(self.context.volume, self.context.root_file, fp_1)

        fp_2 = os.path.join(self.context.root_path, "song2.m4a")
        with open(fp_2, "w+") as f_h:
            f_h.write("a")
        file_2_obj = create_entry(self.context.volume, self.context.root_file, fp_2)

        playlist = create_playlist(self.context.admin, "LOL")
        add_playlist_file(self.context.admin, playlist.id, file_1_obj.id)
        add_playlist_file(self.context.admin, playlist.id, file_2_obj.id)

        pl_file_1 = PlaylistFile.objects.get(file=file_1_obj)
        pl_file_2 = PlaylistFile.objects.get(file=file_2_obj)

        post_data = {"action": "reorder", "files": [pl_file_2.id, pl_file_1.id]}
        self.client.force_login(self.context.admin)
        response = self.client.post(
            f"{self.base_url}{playlist.id}", post_data, "application/json"
        )
        self.assertEqual(http.HTTPStatus.OK, response.status_code)
        self.assertEqual({"id": str(playlist.id), "name": "LOL"}, response.json())

        pl_file_1.refresh_from_db()
        pl_file_2.refresh_from_db()
        self.assertEqual(1, pl_file_1.sequence)
        self.assertEqual(0, pl_file_2.sequence)

    def test_post_6(self):
        """Test POST method"""
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
        playlist = create_playlist(self.user, "LOL")
        self.client.force_login(self.user)
        response = self.client.delete(f"{self.base_url}{playlist.id}")
        self.assertEqual(http.HTTPStatus.OK, response.status_code)
        self.assertEqual({}, response.json())
        self.assertEqual(0, Playlist.objects.count())

    def test_delete_2(self):
        """Test DELETE method (Not owner)"""
        playlist = create_playlist(self.context.admin, "LOL")
        self.client.force_login(self.user)
        response = self.client.delete(f"{self.base_url}{playlist.id}")
        self.assertEqual(http.HTTPStatus.NOT_FOUND, response.status_code)
        self.assertEqual({"error": "Playlist not found."}, response.json())
        self.assertEqual(1, Playlist.objects.count())

    def test_delete_3(self):
        """Test DELETE method (Invalid id)"""
        self.client.force_login(self.context.admin)
        response = self.client.delete(self.url)
        self.assertEqual(http.HTTPStatus.NOT_FOUND, response.status_code)
        self.assertEqual({"error": "Playlist not found."}, response.json())

    def test_delete_4(self):
        """Test DELETE method"""
        response = self.client.delete(self.url)
        self.assertEqual(http.HTTPStatus.FOUND, response.status_code)
        self.assertEqual(b"", response.content)
