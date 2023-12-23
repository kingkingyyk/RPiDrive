import http
import uuid

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import resolve

from rpidrive.controllers.volume import VolumePermissionModel, update_volume_permission
from rpidrive.models import Volume, VolumePermissionEnum, VolumeUser
from rpidrive.views.ui_api.volumes import VolumeDetailView
from rpidrive.tests.helpers.setup import SetupContext


class TestVolumeDetailView(TestCase):  # pylint: disable=too-many-public-methods
    """Test VolumeCreateView"""

    def setUp(self):
        self.url = "/drive/ui-api/volumes/"
        self.context = SetupContext()
        self.user = User.objects.create_user("z")
        self.vol_url = f"{self.url}{self.context.volume.id}"

    def tearDown(self):
        self.context.cleanup()
        User.objects.all().delete()

    def test_url(self):
        """Test url"""
        self.assertEqual(VolumeDetailView, resolve(self.vol_url).func.view_class)

    def test_get_1(self):
        """Test GET method (Admin)"""
        update_volume_permission(
            self.context.admin,
            str(self.context.volume.id),
            [
                VolumePermissionModel(
                    user=self.user.id, permission=VolumePermissionEnum.READ
                )
            ],
        )

        expected = {
            "id": str(self.context.volume.id),
            "name": self.context.volume.name,
            "indexing": self.context.volume.indexing,
            "path": self.context.volume.path,
            "kind": self.context.volume.kind,
            "root_file": str(self.context.root_file.id),
            "permissions": [
                {
                    "user": self.user.id,
                    "permission": VolumePermissionEnum.READ,
                }
            ],
        }

        users = [self.context.admin, self.user]
        for user in users:
            self.client.force_login(user)
            response = self.client.get(self.vol_url)
            self.assertEqual(http.HTTPStatus.OK, response.status_code)
            data = response.json()
            self.assertGreater(data["total_space"], 0)
            self.assertGreater(data["used_space"], 0)
            self.assertGreater(data["free_space"], 0)
            del data["total_space"]
            del data["used_space"]
            del data["free_space"]
            self.assertEqual(expected, data)
            self.client.logout()

    def test_get_2(self):
        """Test GET method (No permission user)"""
        self.client.force_login(self.user)
        response = self.client.get(self.vol_url)
        self.assertEqual(http.HTTPStatus.NOT_FOUND, response.status_code)
        self.assertEqual({"error": "Volume not found."}, response.json())

    def test_get_3(self):
        """Test GET method (No login)"""
        response = self.client.get(self.vol_url)
        self.assertEqual(http.HTTPStatus.FOUND, response.status_code)
        self.assertEqual(b"", response.content)

    def test_get_4(self):
        """Test GET method (Invalid id)"""
        invalid_url = f"{self.url}{uuid.uuid4()}"
        self.client.force_login(self.context.admin)
        response = self.client.get(invalid_url)
        self.assertEqual(http.HTTPStatus.NOT_FOUND, response.status_code)
        self.assertEqual({"error": "Volume not found."}, response.json())

    def test_post_1(self):
        """Test POST method"""
        post_data = {"name": "sigh", "path": "/sys"}
        self.client.force_login(self.context.admin)
        response = self.client.post(self.vol_url, post_data, "application/json")
        self.assertEqual(http.HTTPStatus.OK, response.status_code)
        self.assertEqual({}, response.json())

        self.context.volume.refresh_from_db()
        self.assertEqual(post_data["name"], self.context.volume.name)
        self.assertEqual(post_data["path"], self.context.volume.path)

    def test_post_2(self):
        """Test POST method (Invalid name)"""
        initial = {"name": self.context.volume.name, "path": self.context.volume.path}
        post_data = {"name": "  ", "path": self.context.volume.path}
        self.client.force_login(self.context.admin)
        response = self.client.post(self.vol_url, post_data, "application/json")
        self.assertEqual(http.HTTPStatus.BAD_REQUEST, response.status_code)
        self.assertEqual({"error": "Invalid volume name."}, response.json())

        self.context.volume.refresh_from_db()
        self.assertEqual(initial["name"], self.context.volume.name)
        self.assertEqual(initial["path"], self.context.volume.path)

    def test_post_3(self):
        """Test POST method (Invalid path)"""
        initial = {"name": self.context.volume.name, "path": self.context.volume.path}
        post_data = {"name": "sigh", "path": "/gg"}
        self.client.force_login(self.context.admin)
        response = self.client.post(self.vol_url, post_data, "application/json")
        self.assertEqual(http.HTTPStatus.BAD_REQUEST, response.status_code)
        self.assertEqual({"error": "Path doesn't exist."}, response.json())

        self.context.volume.refresh_from_db()
        self.assertEqual(initial["name"], self.context.volume.name)
        self.assertEqual(initial["path"], self.context.volume.path)

    def test_post_4(self):
        """Test POST method (User in volume)"""
        update_volume_permission(
            self.context.admin,
            str(self.context.volume.id),
            [
                VolumePermissionModel(
                    user=self.user.pk,
                    permission=VolumePermissionEnum.ADMIN,
                )
            ],
        )
        post_data = {"name": "sigh", "path": "/sys"}
        self.client.force_login(self.user)
        response = self.client.post(self.vol_url, post_data, "application/json")
        self.assertEqual(http.HTTPStatus.OK, response.status_code)
        self.assertEqual({}, response.json())

        self.context.volume.refresh_from_db()
        self.assertEqual(post_data["name"], self.context.volume.name)
        self.assertEqual(post_data["path"], self.context.volume.path)

    def test_post_5(self):
        """Test POST method (User in volume)"""
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
        initial = {"name": self.context.volume.name, "path": self.context.volume.path}
        post_data = {"name": "sigh", "path": "/sys"}
        self.client.force_login(self.user)
        response = self.client.post(self.vol_url, post_data, "application/json")
        self.assertEqual(http.HTTPStatus.FORBIDDEN, response.status_code)
        self.assertEqual({"error": "No permission."}, response.json())

        self.context.volume.refresh_from_db()
        self.assertEqual(initial["name"], self.context.volume.name)
        self.assertEqual(initial["path"], self.context.volume.path)

    def test_post_6(self):
        """Test POST method (User not in volume)"""
        initial = {"name": self.context.volume.name, "path": self.context.volume.path}
        post_data = {"name": "sigh", "path": "/sys"}
        self.client.force_login(self.user)
        response = self.client.post(self.vol_url, post_data, "application/json")
        self.assertEqual(http.HTTPStatus.NOT_FOUND, response.status_code)
        self.assertEqual({"error": "Volume not found."}, response.json())

        self.context.volume.refresh_from_db()
        self.assertEqual(initial["name"], self.context.volume.name)
        self.assertEqual(initial["path"], self.context.volume.path)

    def test_post_7(self):
        """Test POST method (No login)"""
        response = self.client.post(self.vol_url)
        self.assertEqual(http.HTTPStatus.FOUND, response.status_code)
        self.assertEqual(b"", response.content)

    def test_post_8(self):
        """Test POST method (Admin updates volume permission)"""
        post_data = {
            "permissions": [
                {
                    "user": self.user.pk,
                    "permission": VolumePermissionEnum.READ,
                }
            ]
        }
        self.client.force_login(self.context.admin)
        response = self.client.post(
            f"{self.vol_url}?fields=permissions", post_data, "application/json"
        )
        self.assertEqual(http.HTTPStatus.OK, response.status_code)
        self.assertEqual({}, response.json())

        self.assertEqual(1, VolumeUser.objects.count())
        v_user = VolumeUser.objects.first()
        self.assertEqual(self.user.id, v_user.user_id)
        self.assertEqual(VolumePermissionEnum.READ, v_user.permission)

    def test_post_9(self):
        """Test POST method (Volume admin updates volume permission)"""
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

        user_2 = User.objects.create_user("c")
        post_data = {
            "permissions": [
                {
                    "user": self.user.id,
                    "permission": VolumePermissionEnum.ADMIN,
                },
                {
                    "user": user_2.id,
                    "permission": VolumePermissionEnum.READ,
                },
            ]
        }
        self.client.force_login(self.user)
        response = self.client.post(
            f"{self.vol_url}?fields=permissions", post_data, "application/json"
        )
        self.assertEqual(http.HTTPStatus.OK, response.status_code)
        self.assertEqual({}, response.json())

        self.assertEqual(2, VolumeUser.objects.count())
        v_user = VolumeUser.objects.last()
        self.assertEqual(user_2.id, v_user.user_id)
        self.assertEqual(VolumePermissionEnum.READ, v_user.permission)

    def test_post_10(self):
        """Test POST method (Volume non-admin user updates volume permission)"""
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

            post_data = {
                "permissions": [
                    {
                        "user": self.user.id,
                        "permission": VolumePermissionEnum.ADMIN,
                    },
                ]
            }
            self.client.force_login(self.user)
            response = self.client.post(
                f"{self.vol_url}?fields=permissions", post_data, "application/json"
            )
            self.assertEqual(http.HTTPStatus.FORBIDDEN, response.status_code)
            self.assertEqual({"error": "No permission."}, response.json())

            self.assertEqual(1, VolumeUser.objects.count())
            v_user = VolumeUser.objects.last()
            self.assertEqual(self.user.id, v_user.user_id)
            self.assertEqual(perm, v_user.permission)

    def test_put_1(self):
        """Test PUT method"""
        self.client.force_login(self.context.admin)
        response = self.client.put(self.vol_url)
        self.assertEqual(http.HTTPStatus.METHOD_NOT_ALLOWED, response.status_code)
        self.assertEqual(b"", response.content)

    def test_put_2(self):
        """Test PUT method"""
        response = self.client.put(self.vol_url)
        self.assertEqual(http.HTTPStatus.FOUND, response.status_code)
        self.assertEqual(b"", response.content)

    def test_delete_1(self):
        """Test DELETE method"""
        self.client.force_login(self.context.admin)
        response = self.client.delete(self.vol_url)
        self.assertEqual(http.HTTPStatus.OK, response.status_code)
        self.assertEqual({}, response.json())
        self.assertEqual(0, Volume.objects.count())

    def test_delete_2(self):
        """Test DELETE method (User not in volume)"""
        self.client.force_login(self.user)
        response = self.client.delete(self.vol_url)
        self.assertEqual(http.HTTPStatus.NOT_FOUND, response.status_code)
        self.assertEqual({"error": "Volume not found."}, response.json())
        self.assertEqual(1, Volume.objects.count())

    def test_delete_3(self):
        """Test DELETE method (User in volume)"""
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
        self.client.force_login(self.user)
        response = self.client.delete(self.vol_url)
        self.assertEqual(http.HTTPStatus.FORBIDDEN, response.status_code)
        self.assertEqual({"error": "No permission."}, response.json())
        self.assertEqual(1, Volume.objects.count())

    def test_delete_4(self):
        """Test DELETE method (No login)"""
        response = self.client.delete(self.vol_url)
        self.assertEqual(http.HTTPStatus.FOUND, response.status_code)
        self.assertEqual(b"", response.content)
        self.assertEqual(1, Volume.objects.count())
