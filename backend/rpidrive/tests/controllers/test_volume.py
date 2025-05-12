import os
import uuid

from django.contrib.auth.models import User
from django.db.models import Q
from django.db.utils import IntegrityError
from django.test import TestCase

from rpidrive.controllers.volume import (
    InvalidVolumeNameException,
    InvalidVolumePathException,
    NoPermissionException,
    VolumeNotFoundException,
    VolumePermissionEnum,
    VolumePermissionModel,
    VolumeUser,
    create_volume,
    delete_volume,
    request_volume,
    get_root_file_id,
    get_volumes,
    get_volume_space,
    perform_index,
    update_volume,
    update_volume_permission,
)
from rpidrive.models import (
    Activity,
    ActivityKindEnum,
    File,
    FileKindEnum,
    Volume,
    VolumeKindEnum,
)


class TestVolumeController(TestCase):  # pylint: disable=too-many-public-methods
    """Test volume controller"""

    def setUp(self):
        self.admin_user = User.objects.create_superuser("hehe")
        self.normal_user = User.objects.create_user("noob")

    def tearDown(self):
        Volume.objects.all().delete()
        User.objects.all().delete()
        Activity.objects.all().delete()

    def test_create_volume_1(self):
        """Test create volume"""
        volume = create_volume(
            self.admin_user, "HEHE", VolumeKindEnum.HOST_PATH, "/var/"
        )
        self.assertEqual(volume.name, "HEHE")
        self.assertEqual(volume.kind, VolumeKindEnum.HOST_PATH)
        self.assertEqual(volume.path, "/var")
        self.assertTrue(
            File.objects.filter(
                Q(volume=volume)
                & Q(path_from_vol=os.path.sep)
                & Q(name="")
                & Q(kind=FileKindEnum.FOLDER)
            ).exists()
        )
        activity = Activity.objects.first()
        self.assertEqual(activity.actor, self.admin_user)
        self.assertEqual(activity.kind, ActivityKindEnum.CREATE_VOLUME)
        self.assertEqual(activity.data, {"volume_id": str(volume.id)})

    def test_create_volume_2(self):
        """Test create volume (Normal user)"""
        self.assertRaises(
            NoPermissionException,
            create_volume,
            self.normal_user,
            "HEHE",
            VolumeKindEnum.HOST_PATH,
            "/var",
        )
        self.assertFalse(Volume.objects.exists())
        self.assertFalse(File.objects.exists())
        self.assertFalse(Activity.objects.exists())

    def test_create_volume_3(self):
        """Test create volume (Parent path added)"""
        create_volume(self.admin_user, "HEHE", VolumeKindEnum.HOST_PATH, "/var")
        self.assertRaises(
            InvalidVolumePathException,
            create_volume,
            self.admin_user,
            "HEHE2",
            VolumeKindEnum.HOST_PATH,
            "/var/lib",
        )

    def test_create_volume_4(self):
        """Test create volume (Child path added)"""
        create_volume(self.admin_user, "HEHE", VolumeKindEnum.HOST_PATH, "/var/lib")
        self.assertRaises(
            InvalidVolumePathException,
            create_volume,
            self.admin_user,
            "HEHE2",
            VolumeKindEnum.HOST_PATH,
            "/var/",
        )

    def test_create_volume_5(self):
        """Test create volume (Path not exists)"""
        self.assertRaises(
            InvalidVolumePathException,
            create_volume,
            self.admin_user,
            "HEHE2",
            VolumeKindEnum.HOST_PATH,
            "/gg!!/",
        )

    def test_create_volume_6(self):
        """Test create volume (Invalid name)"""
        self.assertRaises(
            InvalidVolumeNameException,
            create_volume,
            self.admin_user,
            "",
            VolumeKindEnum.HOST_PATH,
            "/var/",
        )

    def test_create_volume_7(self):
        """Test create volume (Duplicate name)"""
        create_volume(self.admin_user, "HEHE", VolumeKindEnum.HOST_PATH, "/var")
        self.assertRaises(
            IntegrityError,
            create_volume,
            self.admin_user,
            "HEHE",
            VolumeKindEnum.HOST_PATH,
            "/lib",
        )

    def test_create_volume_9(self):
        """Test create volume (Path is file)"""
        self.assertRaises(
            InvalidVolumePathException,
            create_volume,
            self.admin_user,
            "HEHE",
            VolumeKindEnum.HOST_PATH,
            os.path.abspath(__file__),
        )

    def test_create_volume_10(self):
        """Test create volume (Path is link)"""
        link_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "link")
        os.symlink(os.path.abspath(__file__), link_file)
        self.assertRaises(
            InvalidVolumePathException,
            create_volume,
            self.admin_user,
            "HEHE",
            VolumeKindEnum.HOST_PATH,
            link_file,
        )
        os.unlink(link_file)

    def test_get_volumes(self):
        """Test get_volumes"""
        create_volume(self.admin_user, "var", VolumeKindEnum.HOST_PATH, "/var")
        volume_2 = create_volume(
            self.admin_user, "sys", VolumeKindEnum.HOST_PATH, "/sys"
        )
        update_volume_permission(
            self.admin_user,
            volume_2.pk,
            [
                VolumePermissionModel(
                    user=self.normal_user.pk,
                    permission=VolumePermissionEnum.READ,
                )
            ],
        )
        self.assertEqual(get_volumes(self.admin_user).count(), 2)
        self.assertEqual(get_volumes(self.normal_user).count(), 1)

    def test_update_volume_1(self):
        """Test update_volume"""
        volume = create_volume(self.admin_user, "var", VolumeKindEnum.HOST_PATH, "/var")
        update_volume(self.admin_user, volume.pk, "sys", "/sys")
        volume.refresh_from_db()
        self.assertEqual(volume.name, "sys")
        self.assertEqual(volume.path, "/sys")

        self.assertTrue(
            Activity.objects.filter(
                Q(actor=self.admin_user) & Q(kind=ActivityKindEnum.UPDATE_VOLUME)
            ).exists()
        )

        # Read-write permission
        update_volume_permission(
            self.admin_user,
            volume.pk,
            [
                VolumePermissionModel(
                    user=self.normal_user.pk,
                    permission=VolumePermissionEnum.ADMIN,
                )
            ],
        )
        update_volume(self.normal_user, volume.pk, "var", "/var")
        volume.refresh_from_db()
        self.assertEqual(volume.name, "var")
        self.assertEqual(volume.path, "/var")

    def test_update_volume_2(self):
        """Test update_volume (No permission)"""
        volume = create_volume(self.admin_user, "var", VolumeKindEnum.HOST_PATH, "/var")
        self.assertRaises(
            VolumeNotFoundException,
            update_volume,
            self.normal_user,
            volume.pk,
            "sys",
            "/sys",
        )
        volume.refresh_from_db()
        self.assertEqual(volume.name, "var")
        self.assertEqual(volume.path, "/var")

        update_volume_permission(
            self.admin_user,
            volume.pk,
            [
                VolumePermissionModel(
                    user=self.normal_user.pk,
                    permission=VolumePermissionEnum.READ,
                )
            ],
        )
        self.assertRaises(
            NoPermissionException,
            update_volume,
            self.normal_user,
            volume.pk,
            "sys",
            "/sys",
        )
        volume.refresh_from_db()
        self.assertEqual(volume.name, "var")
        self.assertEqual(volume.path, "/var")

    def test_update_volume_3(self):
        """Test update_volume (Invalid name)"""
        volume = create_volume(self.admin_user, "var", VolumeKindEnum.HOST_PATH, "/var")
        create_volume(self.admin_user, "sys", VolumeKindEnum.HOST_PATH, "/sys")
        self.assertRaises(
            IntegrityError, update_volume, self.admin_user, volume.pk, "sys", "/lib"
        )

    def test_update_volume_4(self):
        """Test update_volume (Invalid path)"""
        volume = create_volume(self.admin_user, "var", VolumeKindEnum.HOST_PATH, "/var")
        create_volume(self.admin_user, "sys", VolumeKindEnum.HOST_PATH, "/sys")
        self.assertRaises(
            InvalidVolumePathException,
            update_volume,
            self.admin_user,
            volume.pk,
            "var",
            "/zz",
        )

    def test_update_volume_5(self):
        """Test update_volume (Empty name)"""
        volume = create_volume(self.admin_user, "var", VolumeKindEnum.HOST_PATH, "/var")
        self.assertRaises(
            InvalidVolumeNameException,
            update_volume,
            self.admin_user,
            volume.pk,
            "",
            "/lib",
        )

    def test_update_volume_6(self):
        """Test update_volume (Truncate path sep)"""
        volume = create_volume(self.admin_user, "var", VolumeKindEnum.HOST_PATH, "/var")
        update_volume(self.admin_user, volume.pk, "sys", "/sys//")
        volume.refresh_from_db()
        self.assertEqual(volume.name, "sys")
        self.assertEqual(volume.path, "/sys")

    def test_update_volume_p_1(self):
        """Test get_volume_permission"""
        volume = create_volume(self.admin_user, "var", VolumeKindEnum.HOST_PATH, "/var")
        update_volume_permission(
            self.admin_user,
            volume.pk,
            [
                VolumePermissionModel(
                    user=self.admin_user.pk,
                    permission=VolumePermissionEnum.READ,
                )
            ],
        )
        self.assertEqual(get_volumes(self.admin_user).count(), 1)

    def test_update_volume_p_2(self):
        """Test get_volume_permission (2)"""
        volume = create_volume(self.admin_user, "var", VolumeKindEnum.HOST_PATH, "/var")
        self.assertEqual(get_volumes(self.normal_user).count(), 0)
        update_volume_permission(
            self.admin_user,
            volume.pk,
            [
                VolumePermissionModel(
                    user=self.normal_user.pk,
                    permission=VolumePermissionEnum.READ,
                )
            ],
        )
        self.assertEqual(get_volumes(self.normal_user).count(), 1)

    def test_update_volume_p_3(self):
        """Test get_volume_permission (No permission)"""
        volume = create_volume(self.admin_user, "var", VolumeKindEnum.HOST_PATH, "/var")
        update_volume_permission(
            self.admin_user,
            volume.pk,
            [
                VolumePermissionModel(
                    user=self.normal_user.pk,
                    permission=VolumePermissionEnum.READ,
                )
            ],
        )

        # Can't update permission with read-only role
        self.assertRaises(
            NoPermissionException,
            update_volume_permission,
            self.normal_user,
            volume.pk,
            [
                VolumePermissionModel(
                    user=self.normal_user.pk,
                    permission=VolumePermissionEnum.READ_WRITE,
                )
            ],
        )

    def test_update_volume_p_4(self):
        """Test get_volume_permission (Can't reduce self permission)"""
        volume = create_volume(self.admin_user, "var", VolumeKindEnum.HOST_PATH, "/var")
        update_volume_permission(
            self.admin_user,
            volume.pk,
            [
                VolumePermissionModel(
                    user=self.normal_user.pk,
                    permission=VolumePermissionEnum.ADMIN,
                )
            ],
        )

        # Can't update permission with read-only role
        update_volume_permission(
            self.normal_user,
            volume.pk,
            [
                VolumePermissionModel(
                    user=self.normal_user.pk,
                    permission=VolumePermissionEnum.READ,
                )
            ],
        )
        self.assertEqual(
            VolumeUser.objects.filter(volume=volume, user=self.normal_user)
            .first()
            .permission,
            VolumePermissionEnum.ADMIN,
        )

    def test_delete_volume_1(self):
        """Test delete_volume"""
        volume = create_volume(self.admin_user, "var", VolumeKindEnum.HOST_PATH, "/var")
        delete_volume(self.admin_user, volume.pk)
        self.assertFalse(Volume.objects.exists())
        self.assertTrue(
            Activity.objects.filter(
                actor=self.admin_user, kind=ActivityKindEnum.DELETE_VOLUME
            ).exists()
        )

    def test_delete_volume_2(self):
        """Test delete_volume (2)"""
        volume = create_volume(self.admin_user, "var", VolumeKindEnum.HOST_PATH, "/var")

        # Can't delete with read/read-write
        perms = [
            VolumePermissionEnum.READ,
            VolumePermissionEnum.READ_WRITE,
        ]
        for perm in perms:
            update_volume_permission(
                self.admin_user,
                volume.pk,
                [
                    VolumePermissionModel(
                        user=self.normal_user.pk,
                        permission=perm,
                    )
                ],
            )
            self.assertRaises(
                NoPermissionException, delete_volume, self.normal_user, volume.pk
            )
            self.assertTrue(Volume.objects.exists())

        # Allow deletion with admin
        update_volume_permission(
            self.admin_user,
            volume.pk,
            [
                VolumePermissionModel(
                    user=self.normal_user.pk,
                    permission=VolumePermissionEnum.ADMIN,
                )
            ],
        )
        delete_volume(self.normal_user, volume.pk)
        self.assertFalse(Volume.objects.exists())
        self.assertTrue(
            Activity.objects.filter(
                actor=self.normal_user, kind=ActivityKindEnum.DELETE_VOLUME
            ).exists()
        )

    def test_get_volume_1(self):
        """Test get_volume"""
        volume = create_volume(self.admin_user, "var", VolumeKindEnum.HOST_PATH, "/var")
        self.assertIsNotNone(
            request_volume(self.admin_user, volume.pk, VolumePermissionEnum.READ, True)
        )
        update_volume_permission(
            self.admin_user,
            volume.pk,
            [
                VolumePermissionModel(
                    user=self.normal_user.pk,
                    permission=VolumePermissionEnum.READ,
                )
            ],
        )
        self.assertIsNotNone(
            request_volume(self.normal_user, volume.pk, VolumePermissionEnum.READ, True)
        )

    def test_get_volume_2(self):
        """Test get_volume"""
        volume = create_volume(self.admin_user, "var", VolumeKindEnum.HOST_PATH, "/var")
        self.assertRaises(
            VolumeNotFoundException,
            request_volume,
            self.normal_user,
            volume.pk,
            VolumePermissionEnum.READ,
            True,
        )

    def test_get_volume_3(self):
        """Test get_volume (Not exists)"""
        self.assertRaises(
            VolumeNotFoundException,
            request_volume,
            self.normal_user,
            str(uuid.uuid4()),
            VolumePermissionEnum.READ,
            True,
        )

    def test_get_volume_space_1(self):
        """Test get_volume_space 1"""
        volume = create_volume(self.admin_user, "var", VolumeKindEnum.HOST_PATH, "/var")
        total, used, free = get_volume_space(volume)
        self.assertTrue(isinstance(total, int))
        self.assertGreater(total, 0)
        self.assertTrue(isinstance(used, int))
        self.assertGreater(used, 0)
        self.assertTrue(isinstance(free, int))
        self.assertGreater(free, 0)

    def test_get_volume_space_2(self):
        """Test get_volume_space 2"""
        total, used, free = get_volume_space("/var")
        self.assertTrue(isinstance(total, int))
        self.assertGreater(total, 0)
        self.assertTrue(isinstance(used, int))
        self.assertGreater(used, 0)
        self.assertTrue(isinstance(free, int))
        self.assertGreater(free, 0)

    def test_get_volume_space_3(self):
        """Test get_volume_space 3"""
        total, used, free = get_volume_space("/gg")
        self.assertTrue(isinstance(total, int))
        self.assertEqual(0, total)
        self.assertTrue(isinstance(used, int))
        self.assertEqual(0, used)
        self.assertTrue(isinstance(free, int))
        self.assertEqual(0, free)

    def test_get_root_file_id(self):
        """Test get_root_file_id"""
        volume = create_volume(self.admin_user, "var", VolumeKindEnum.HOST_PATH, "/var")
        file_id = get_root_file_id(volume)
        self.assertIsNotNone(file_id)

        file = File.objects.get(pk=file_id)
        self.assertEqual(volume.id, file.volume_id)
        self.assertIsNone(file.parent)

    def test_perform_index_1(self):
        """Test perform_index"""
        volume = create_volume(self.admin_user, "var", VolumeKindEnum.HOST_PATH, "/var")
        volume.indexing = False
        volume.save()

        perform_index(self.admin_user, volume.id)
        volume.refresh_from_db()
        self.assertTrue(volume.indexing)

    def test_perform_index_2(self):
        """Test perform_index (No permission)"""
        volume = create_volume(self.admin_user, "var", VolumeKindEnum.HOST_PATH, "/var")
        volume.indexing = False
        volume.save()

        with self.assertRaises(VolumeNotFoundException):
            perform_index(self.normal_user, volume.id)
        volume.refresh_from_db()
        self.assertFalse(volume.indexing)

    def test_perform_index_3(self):
        """Test perform_index (Write user)"""
        volume = create_volume(self.admin_user, "var", VolumeKindEnum.HOST_PATH, "/var")
        volume.indexing = False
        volume.save()

        update_volume_permission(
            self.admin_user,
            volume.pk,
            [
                VolumePermissionModel(
                    user=self.normal_user.pk,
                    permission=VolumePermissionEnum.READ_WRITE,
                )
            ],
        )

        with self.assertRaises(NoPermissionException):
            perform_index(self.normal_user, volume.id)
        volume.refresh_from_db()
        self.assertFalse(volume.indexing)
