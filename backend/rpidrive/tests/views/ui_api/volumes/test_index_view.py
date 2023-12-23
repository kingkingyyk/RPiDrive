import http
import uuid

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import resolve

from rpidrive.controllers.volume import VolumePermissionModel, update_volume_permission
from rpidrive.models import VolumePermissionEnum
from rpidrive.views.ui_api.volumes import VolumeIndexView
from rpidrive.tests.helpers.setup import SetupContext


class TestVolumeIndexView(TestCase):
    """Test VolumeIndexView"""

    @classmethod
    def _construct_url(cls, volume_id: str):
        return f"/drive/ui-api/volumes/{volume_id}/index"

    def setUp(self):
        self.context = SetupContext()
        self.user = User.objects.create_user("z")

    def tearDown(self):
        self.context.cleanup()
        User.objects.all().delete()

    def test_url(self):
        """Test url"""
        self.assertEqual(
            VolumeIndexView,
            resolve(self._construct_url(self.context.volume.id)).func.view_class,
        )

    def test_post_1(self):
        """Test POST method (System admin)"""
        self.context.volume.indexing = False
        self.context.volume.save(update_fields=["indexing"])

        self.client.force_login(self.context.admin)
        response = self.client.post(self._construct_url(self.context.volume.id))
        self.assertEqual(http.HTTPStatus.OK, response.status_code)
        self.assertEqual({}, response.json())

        self.context.volume.refresh_from_db()
        self.assertTrue(self.context.volume.indexing)

    def test_post_2(self):
        """Test POST method (Read/Read-Write)"""
        self.context.volume.indexing = False
        self.context.volume.save(update_fields=["indexing"])

        permissions = [VolumePermissionEnum.READ, VolumePermissionEnum.READ_WRITE]
        for perm in permissions:
            update_volume_permission(
                self.context.admin,
                str(self.context.volume.id),
                [
                    VolumePermissionModel(
                        user=self.user.id,
                        permission=perm,
                    )
                ],
            )
            self.client.force_login(self.user)
            response = self.client.post(self._construct_url(self.context.volume.id))
            self.assertEqual(http.HTTPStatus.FORBIDDEN, response.status_code)
            self.assertEqual({"error": "No permission."}, response.json())

            self.context.volume.refresh_from_db()
            self.assertFalse(self.context.volume.indexing)
            self.client.logout()

    def test_post_3(self):
        """Test POST method (Volume admin)"""
        self.context.volume.indexing = False
        self.context.volume.save(update_fields=["indexing"])

        update_volume_permission(
            self.context.admin,
            str(self.context.volume.id),
            [
                VolumePermissionModel(
                    user=self.user.id,
                    permission=VolumePermissionEnum.ADMIN,
                )
            ],
        )

        self.client.force_login(self.user)
        response = self.client.post(self._construct_url(self.context.volume.id))
        self.assertEqual(http.HTTPStatus.OK, response.status_code)
        self.assertEqual({}, response.json())

        self.context.volume.refresh_from_db()
        self.assertTrue(self.context.volume.indexing)

    def test_post_4(self):
        """Test POST method (No login)"""
        response = self.client.post(self._construct_url(self.context.volume.id))
        self.assertEqual(http.HTTPStatus.FOUND, response.status_code)
        self.assertEqual(b"", response.content)

    def test_post_5(self):
        """Test POST method (Invalid id)"""
        self.client.force_login(self.context.admin)
        response = self.client.post(self._construct_url(str(uuid.uuid4())))
        self.assertEqual(http.HTTPStatus.NOT_FOUND, response.status_code)
        self.assertEqual({"error": "Volume not found."}, response.json())

        self.context.volume.refresh_from_db()
        self.assertTrue(self.context.volume.indexing)

    def test_get_1(self):
        """Test GET method"""
        self.client.force_login(self.context.admin)
        response = self.client.get(self._construct_url(self.context.volume.id))
        self.assertEqual(http.HTTPStatus.METHOD_NOT_ALLOWED, response.status_code)
        self.assertEqual(b"", response.content)

    def test_get_2(self):
        """Test GET method (No login)"""
        response = self.client.get(self._construct_url(self.context.volume.id))
        self.assertEqual(http.HTTPStatus.FOUND, response.status_code)
        self.assertEqual(b"", response.content)

    def test_put_1(self):
        """Test PUT method"""
        self.client.force_login(self.context.admin)
        response = self.client.put(self._construct_url(self.context.volume.id))
        self.assertEqual(http.HTTPStatus.METHOD_NOT_ALLOWED, response.status_code)
        self.assertEqual(b"", response.content)

    def test_put_2(self):
        """Test PUT method"""
        response = self.client.put(self._construct_url(self.context.volume.id))
        self.assertEqual(http.HTTPStatus.FOUND, response.status_code)
        self.assertEqual(b"", response.content)

    def test_delete_1(self):
        """Test DELETE method"""
        self.client.force_login(self.context.admin)
        response = self.client.delete(self._construct_url(self.context.volume.id))
        self.assertEqual(http.HTTPStatus.METHOD_NOT_ALLOWED, response.status_code)
        self.assertEqual(b"", response.content)

    def test_delete_2(self):
        """Test DELETE method"""
        response = self.client.delete(self._construct_url(self.context.volume.id))
        self.assertEqual(http.HTTPStatus.FOUND, response.status_code)
        self.assertEqual(b"", response.content)
