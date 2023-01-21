import http
import tempfile
import uuid

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from drive.core.storage_provider import create_storage_provider_helper
from drive.models import (
    LocalFileObject,
    Playlist,
    PlaylistFile,
    StorageProvider,
    StorageProviderTypeEnum,
)
from drive.tests.web.shared import MIMETYPE_JSON

class TestPlaylist(TestCase): # pylint: disable=too-many-instance-attributes
    """Test playlist views"""

    def _get_manage_url(self, i_d: str) -> str:
        return reverse('playlist.manage', args=[i_d])

    def setUp(self):
        self.user_1 = User.objects.create_user('user_1')
        self.user_2 = User.objects.create_user('user_2')

        self.list_url = reverse('playlist.list')
        self.create_url = reverse('playlist.create')

        self.s_p, self.root = create_storage_provider_helper(
            name='folder',
            sp_type=StorageProviderTypeEnum.LOCAL_PATH.value,
            path=tempfile.gettempdir(),
        )
        self.file_1 = LocalFileObject.objects.create(
            name='love me like u do.m4a',
            obj_type='',
            parent=self.root,
            storage_provider=self.s_p,
            metadata=dict(
                artist='ellie goulding'
            ),
            rel_path='love me like u do.m4a',
            type='music',
        )
        self.file_2 = LocalFileObject.objects.create(
            name='all out of love.m4a',
            obj_type='',
            parent=self.root,
            storage_provider=self.s_p,
            metadata=dict(
                artist='air supply'
            ),
            rel_path='all out of love.m4a',
            type='music',
        )

    def tearDown(self):
        StorageProvider.objects.all().delete()
        Playlist.objects.all().delete()
        User.objects.all().delete()

    def test_list_url(self):
        """Test get_playlists url"""
        self.assertEqual(
            '/drive/web-api/playlists',
            self.list_url
        )

    def test_list_methods(self):
        """Test get_playlists methods"""
        # Not logged in
        response = self.client.get(self.list_url)
        self.assertEqual(http.HTTPStatus.UNAUTHORIZED, response.status_code)

        response = self.client.post(self.list_url)
        self.assertEqual(http.HTTPStatus.UNAUTHORIZED, response.status_code)

        response = self.client.put(self.list_url)
        self.assertEqual(http.HTTPStatus.UNAUTHORIZED, response.status_code)

        response = self.client.delete(self.list_url)
        self.assertEqual(http.HTTPStatus.UNAUTHORIZED, response.status_code)

        # Logged in
        self.client.force_login(self.user_1)
        response = self.client.post(self.list_url)
        self.assertEqual(http.HTTPStatus.METHOD_NOT_ALLOWED, response.status_code)

        response = self.client.put(self.list_url)
        self.assertEqual(http.HTTPStatus.METHOD_NOT_ALLOWED, response.status_code)

        response = self.client.delete(self.list_url)
        self.assertEqual(http.HTTPStatus.METHOD_NOT_ALLOWED, response.status_code)

    def test_list(self):
        """Test get_playlists"""
        playlist_1 = Playlist.objects.create(
            name='user 1 playlist',
            owner=self.user_1,
        )
        PlaylistFile.objects.create(
            playlist=playlist_1,
            file=self.file_1,
            sequence=0,
        )
        playlist_2 = Playlist.objects.create(
            name='user 2 playlist',
            owner=self.user_2,
        )
        PlaylistFile.objects.create(
            playlist=playlist_2,
            file=self.file_2,
            sequence=0,
        )

        # Login as user_1 and check
        self.client.force_login(self.user_1)
        response = self.client.get(self.list_url)
        self.assertEqual(http.HTTPStatus.OK, response.status_code)
        self.assertEqual(
            dict(
                values=[
                    dict(
                        id=str(playlist_1.pk),
                        name=playlist_1.name,
                        files=None,
                    )
                ]
            ), response.json()
        )

        # Login as user_2 and check
        self.client.force_login(self.user_2)
        response = self.client.get(self.list_url)
        self.assertEqual(http.HTTPStatus.OK, response.status_code)
        self.assertEqual(
            dict(
                values=[
                    dict(
                        id=str(playlist_2.pk),
                        name=playlist_2.name,
                        files=None,
                    )
                ]
            ), response.json()
        )

    def test_create_url(self):
        """Test create_playlist url"""
        self.assertEqual(
            '/drive/web-api/playlists/create',
            self.create_url,
        )

    def test_create_methods(self):
        """Test create_playlist methods"""
        # Not logged in
        response = self.client.get(self.create_url)
        self.assertEqual(http.HTTPStatus.UNAUTHORIZED, response.status_code)

        response = self.client.post(self.create_url)
        self.assertEqual(http.HTTPStatus.UNAUTHORIZED, response.status_code)

        response = self.client.put(self.create_url)
        self.assertEqual(http.HTTPStatus.UNAUTHORIZED, response.status_code)

        response = self.client.delete(self.create_url)
        self.assertEqual(http.HTTPStatus.UNAUTHORIZED, response.status_code)

        # Logged in
        self.client.force_login(self.user_1)
        response = self.client.get(self.create_url)
        self.assertEqual(http.HTTPStatus.METHOD_NOT_ALLOWED, response.status_code)

        response = self.client.put(self.create_url)
        self.assertEqual(http.HTTPStatus.METHOD_NOT_ALLOWED, response.status_code)

        response = self.client.delete(self.create_url)
        self.assertEqual(http.HTTPStatus.METHOD_NOT_ALLOWED, response.status_code)

    def test_create(self):
        """Test create_playlist"""
        self.client.force_login(self.user_1)
        response = self.client.post(
            self.create_url,
            dict(name='abc'),
            content_type=MIMETYPE_JSON,
        )
        playlist = Playlist.objects.first()
        self.assertEqual('abc', playlist.name)
        self.assertEqual(http.HTTPStatus.CREATED, response.status_code)
        self.assertEqual(
            dict(
                id=str(playlist.pk),
                name=playlist.name,
                files=[],
            ), response.json()
        )

    def test_manage_url(self):
        """Test manage_playlist url"""
        self.assertEqual(
            '/drive/web-api/playlists/NAH',
            self._get_manage_url('NAH'),
        )

    def test_manage_methods(self):
        """Test manage_playlist methods"""
        url = self._get_manage_url(str(uuid.uuid4()))

        # Not logged in
        response = self.client.get(url)
        self.assertEqual(http.HTTPStatus.UNAUTHORIZED, response.status_code)

        response = self.client.post(url)
        self.assertEqual(http.HTTPStatus.UNAUTHORIZED, response.status_code)

        response = self.client.put(url)
        self.assertEqual(http.HTTPStatus.UNAUTHORIZED, response.status_code)

        response = self.client.delete(url)
        self.assertEqual(http.HTTPStatus.UNAUTHORIZED, response.status_code)

        # Logged in
        self.client.force_login(self.user_1)
        response = self.client.put(url)
        self.assertEqual(http.HTTPStatus.METHOD_NOT_ALLOWED, response.status_code)

    def test_manage(self):
        """Test manage_playlist"""
        playlist_1 = Playlist.objects.create(
            name='user 1 playlist',
            owner=self.user_1,
        )
        PlaylistFile.objects.create(
            playlist=playlist_1,
            file=self.file_1,
            sequence=0,
        )
        playlist_2 = Playlist.objects.create(
            name='user 2 playlist',
            owner=self.user_2,
        )
        self.client.force_login(self.user_1)

        # Get invalid playlist
        response = self.client.get(self._get_manage_url(str(uuid.uuid4())))
        self.assertEqual(http.HTTPStatus.NOT_FOUND, response.status_code)
        self.assertEqual(dict(error='Playlist not found.'), response.json())

        # Get playlist owned by other user
        response = self.client.get(self._get_manage_url(playlist_2.pk))
        self.assertEqual(http.HTTPStatus.NOT_FOUND, response.status_code)
        self.assertEqual(dict(error='Playlist not found.'), response.json())

        # Get valid playlist
        response = self.client.get(self._get_manage_url(playlist_1.pk))
        self.assertEqual(http.HTTPStatus.OK, response.status_code)
        self.assertEqual(dict(
            id=str(playlist_1.pk),
            name=playlist_1.name,
            files=[
                dict(
                    fullPath=f'{tempfile.gettempdir()}/{self.file_1.rel_path}',
                    id=str(self.file_1.pk),
                    metadata=dict(
                        artist='ellie goulding',
                    ),
                    type='music',
                    name=self.file_1.name,
                )
            ]
        ), response.json())

        # Update playlist name
        response = self.client.post(
            self._get_manage_url(playlist_1.pk),
            dict(
                name='blahblah',
            ),
            content_type=MIMETYPE_JSON,
        )
        self.assertEqual(http.HTTPStatus.OK, response.status_code)
        self.assertEqual({}, response.json())
        playlist_1.refresh_from_db()
        self.assertEqual('blahblah', playlist_1.name)

        # Update other user's playlist name
        response = self.client.post(
            self._get_manage_url(playlist_2.pk),
            dict(
                name='blahblah',
            ),
            content_type=MIMETYPE_JSON,
        )
        self.assertEqual(http.HTTPStatus.NOT_FOUND, response.status_code)
        self.assertEqual(dict(error='Playlist not found.'), response.json())

        # Update playlist files
        response = self.client.post(
            self._get_manage_url(playlist_1.pk),
            dict(
                files=[
                    str(self.file_2.pk),
                    str(self.file_1.pk),
                ],
            ),
            content_type=MIMETYPE_JSON
        )
        self.assertEqual(http.HTTPStatus.OK, response.status_code)
        self.assertEqual({}, response.json())
        p_files = list(
            PlaylistFile.objects
            .filter(playlist=playlist_1)
            .order_by('sequence')
            .values_list('file__pk', flat=True)
        )
        self.assertEqual(
            [str(self.file_2.pk), str(self.file_1.pk)],
            [str(x) for x in p_files],
        )

        # Update other user's playlist files
        response = self.client.post(
            self._get_manage_url(playlist_2.pk),
            dict(
                files=[
                    str(self.file_1.pk),
                    str(self.file_2.pk),
                ],
            ),
            content_type=MIMETYPE_JSON
        )
        self.assertEqual(http.HTTPStatus.NOT_FOUND, response.status_code)
        self.assertEqual(dict(error='Playlist not found.'), response.json())
        p_files_count = (
            PlaylistFile.objects
            .filter(playlist=playlist_2)
            .order_by('sequence')
            .count()
        )
        self.assertEqual(0, p_files_count)

        # Delete playlist
        response = self.client.delete(self._get_manage_url(playlist_1.pk))
        self.assertEqual(http.HTTPStatus.OK, response.status_code)
        self.assertEqual({}, response.json())
        self.assertFalse(Playlist.objects.filter(pk=playlist_1.pk).exists())
        self.assertTrue(Playlist.objects.filter(pk=playlist_2.pk).exists())

        # Delete other user's playlist
        response = self.client.delete(self._get_manage_url(playlist_2.pk))
        self.assertEqual(http.HTTPStatus.NOT_FOUND, response.status_code)
        self.assertEqual(dict(error='Playlist not found.'), response.json())
        self.assertTrue(Playlist.objects.filter(pk=playlist_2.pk).exists())
