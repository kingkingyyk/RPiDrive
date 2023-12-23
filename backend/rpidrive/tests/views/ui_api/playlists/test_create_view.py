import http

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import resolve

from rpidrive.models import Playlist
from rpidrive.tests.helpers.setup import SetupContext
from rpidrive.views.ui_api.playlists import PlaylistCreateView


class TestPlaylistCreateView(TestCase):
    """Test playlist create view"""

    def setUp(self):
        self.url = "/drive/ui-api/playlists/create"
        self.context = SetupContext()
        self.user = User.objects.create_user("z")

    def tearDown(self):
        self.context.cleanup()
        User.objects.all().delete()

    def test_url(self):
        """Test url"""
        self.assertEqual(PlaylistCreateView, resolve(self.url).func.view_class)

    def test_post_1(self):
        """Test POST method"""
        self.client.force_login(self.user)
        post_data = {"name": "ZZ  "}
        response = self.client.post(self.url, post_data, "application/json")
        self.assertEqual(http.HTTPStatus.CREATED, response.status_code)
        data = response.json()

        self.assertEqual(1, Playlist.objects.count())
        playlist = Playlist.objects.first()
        self.assertEqual("ZZ", playlist.name)
        self.assertEqual(
            {
                "id": str(playlist.id),
                "name": playlist.name,
            },
            data,
        )

    def test_post_2(self):
        """Test POST method (Invalid name)"""
        self.client.force_login(self.user)
        post_data = {"name": "  "}
        response = self.client.post(self.url, post_data, "application/json")
        self.assertEqual(http.HTTPStatus.BAD_REQUEST, response.status_code)
        self.assertEqual({"error": "Invalid name."}, response.json())
        self.assertEqual(0, Playlist.objects.count())

    def test_post_3(self):
        """Test POST method (Invalid name 2)"""
        self.client.force_login(self.user)
        post_data = {"name": ""}
        response = self.client.post(self.url, post_data, "application/json")
        self.assertEqual(http.HTTPStatus.BAD_REQUEST, response.status_code)
        self.assertEqual({"error": "Invalid name."}, response.json())
        self.assertEqual(0, Playlist.objects.count())

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
