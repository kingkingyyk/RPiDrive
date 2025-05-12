# pylint: disable=too-many-lines
import uuid
import os
from datetime import timedelta

from django.conf import settings
from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone

from rpidrive.controllers.file import (
    File,
    FileNotFoundException,
    compress_files,
    create_folder,
    delete_files,
    get_file,
    get_file_full_path,
    get_file_parents,
    move_files,
    rename_file,
    search_files,
    share_file,
)
from rpidrive.controllers.exceptions import (
    InvalidFileNameException,
    InvalidOperationRequestException,
    NoPermissionException,
)
from rpidrive.controllers.local_file import create_entry
from rpidrive.controllers.volume import (
    VolumeNotFoundException,
    VolumePermissionEnum,
    VolumePermissionModel,
    update_volume_permission,
)
from rpidrive.models import JobKind, VolumeKindEnum
from rpidrive.tests.helpers.setup import SetupContext


class TestFile(TestCase):  # pylint: disable=too-many-public-methods
    """Test file controller"""

    def setUp(self):
        self.context = SetupContext()
        self.context_2 = None

    def tearDown(self):
        self.context.cleanup()
        if self.context_2:
            self.context_2.cleanup()
        User.objects.all().delete()

    def test_get_file_1(self):
        """Test get_file 1"""
        file = get_file(self.context.admin, self.context.root_file.id)
        self.assertIsNotNone(file)
        self.assertEqual(self.context.root_file.id, file.id)

    def test_get_file_2(self):
        """Test get_file 2"""
        normal_user = User.objects.create_user("gg")
        with self.assertRaises(FileNotFoundException):
            get_file(normal_user, self.context.root_file.id)

    def test_get_file_3(self):
        """Test get_file 3"""
        with self.assertRaises(FileNotFoundException):
            get_file(self.context.admin, str(uuid.uuid4()))

    def test_get_file_4(self):
        """Test get_file 4"""
        normal_user = User.objects.create_user("gg")
        perm_model = [
            VolumePermissionModel(
                user=normal_user.id,
                permission=VolumePermissionEnum.READ,
            )
        ]
        update_volume_permission(self.context.admin, self.context.volume.id, perm_model)
        file = get_file(normal_user, self.context.root_file.id)
        self.assertIsNotNone(file)

        # Request write with read-only user
        with self.assertRaises(FileNotFoundException):
            get_file(self.context.admin, str(uuid.uuid4()), write=True)

    def test_get_file_5(self):
        """Test get_file 5"""
        file = get_file(
            self.context.admin,
            self.context.root_file.id,
            ["volume"],
            ["publicfilelink_set"],
        )
        self.assertIsNotNone(file)

    def test_get_file_parent_1(self):
        """Test get_file_parents 1"""
        self.assertEqual([], get_file_parents(self.context.root_file))

        folder1_name = "example"
        folder1_path = os.path.join(self.context.root_path, folder1_name)
        os.makedirs(folder1_path)
        folder1_obj = create_entry(
            self.context.volume,
            self.context.root_file,
            folder1_path,
        )
        self.assertEqual([self.context.root_file], get_file_parents(folder1_obj))

        folder2_name = "anya"
        folder2_path = os.path.join(folder1_path, folder2_name)
        os.makedirs(folder2_path)
        folder2_obj = create_entry(
            self.context.volume,
            folder1_obj,
            folder2_path,
        )
        self.assertEqual(
            [self.context.root_file, folder1_obj], get_file_parents(folder2_obj)
        )

    def test_get_file_parent_2(self):
        """Test get_file_parents 2"""
        self.context.volume.kind = VolumeKindEnum.REMOTE_RPI_DRIVE
        self.context.volume.save()

        with self.assertRaises(NotImplementedError):
            get_file_parents(self.context.root_file)

    def test_delete_files_1(self):
        """Test delete_files (Mixed volumes)"""
        self.context_2 = SetupContext()
        with self.assertRaises(InvalidOperationRequestException):
            delete_files(
                self.context.admin,
                [self.context.root_file.id, self.context_2.root_file.id],
            )

    def test_delete_files_2(self):
        """Test delete_files 2"""
        self.context.volume.kind = VolumeKindEnum.REMOTE_RPI_DRIVE
        self.context.volume.save()
        with self.assertRaises(NotImplementedError):
            delete_files(self.context.admin, [self.context.root_file.id])

    def test_delete_files_3(self):
        """Test delete_files (System admin user)"""
        folder_path = os.path.join(self.context.root_path, "example")
        os.makedirs(folder_path)
        folder_obj = create_entry(
            self.context.volume,
            self.context.root_file,
            folder_path,
        )

        delete_files(self.context.admin, [folder_obj.id])
        self.assertEqual(1, File.objects.count())
        self.assertTrue(File.objects.filter(id=self.context.root_file.id).exists())
        self.assertFalse(os.path.exists(folder_path))

    def test_delete_files_4(self):
        """Test delete_files (No role)"""
        folder_path = os.path.join(self.context.root_path, "example")
        os.makedirs(folder_path)
        folder_obj = create_entry(
            self.context.volume,
            self.context.root_file,
            folder_path,
        )
        normal_user = User.objects.create_user("anya")
        with self.assertRaises(VolumeNotFoundException):
            delete_files(normal_user, [folder_obj.id])

        self.assertEqual(2, File.objects.count())
        self.assertTrue(os.path.exists(folder_path))

    def test_delete_files_5(self):
        """Test delete_files (Read-only user)"""
        folder_path = os.path.join(self.context.root_path, "example")
        os.makedirs(folder_path)
        folder_obj = create_entry(
            self.context.volume,
            self.context.root_file,
            folder_path,
        )
        normal_user = User.objects.create_user("anya")
        update_volume_permission(
            self.context.admin,
            self.context.volume.id,
            [
                VolumePermissionModel(
                    user=normal_user.id,
                    permission=VolumePermissionEnum.READ,
                )
            ],
        )
        with self.assertRaises(NoPermissionException):
            delete_files(normal_user, [folder_obj.id])

        self.assertEqual(2, File.objects.count())
        self.assertTrue(os.path.exists(folder_path))

    def test_delete_files_6(self):
        """Test delete_files (Volume read-write user)"""
        folder_path = os.path.join(self.context.root_path, "example")
        os.makedirs(folder_path)
        folder_obj = create_entry(
            self.context.volume,
            self.context.root_file,
            folder_path,
        )
        normal_user = User.objects.create_user("anya")
        update_volume_permission(
            self.context.admin,
            self.context.volume.id,
            [
                VolumePermissionModel(
                    user=normal_user.id,
                    permission=VolumePermissionEnum.READ_WRITE,
                )
            ],
        )
        delete_files(normal_user, [folder_obj.id])
        self.assertFalse(os.path.exists(folder_path))
        self.assertEqual(1, File.objects.count())
        self.assertTrue(File.objects.filter(id=self.context.root_file.id).exists())

    def test_delete_files_7(self):
        """Test delete_files (Volume admin user)"""
        folder_path = os.path.join(self.context.root_path, "example")
        os.makedirs(folder_path)
        folder_obj = create_entry(
            self.context.volume,
            self.context.root_file,
            folder_path,
        )
        normal_user = User.objects.create_user("anya")
        update_volume_permission(
            self.context.admin,
            self.context.volume.id,
            [
                VolumePermissionModel(
                    user=normal_user.id,
                    permission=VolumePermissionEnum.ADMIN,
                )
            ],
        )
        delete_files(normal_user, [folder_obj.id])
        self.assertFalse(os.path.exists(folder_path))
        self.assertEqual(1, File.objects.count())
        self.assertTrue(File.objects.filter(id=self.context.root_file.id).exists())

    def test_delete_files_8(self):
        """Test delete_files (Non-existence file)"""
        with self.assertRaises(FileNotFoundException):
            delete_files(self.context.admin, [str(uuid.uuid4())])

    def test_delete_files_9(self):
        """Test delete_files (Root file)"""
        with self.assertRaises(InvalidOperationRequestException):
            delete_files(self.context.admin, [self.context.root_file.id])

    def test_rename_file_1(self):
        """Test rename_file"""
        folder_name = "example"
        folder_path = os.path.join(self.context.root_path, folder_name)
        os.makedirs(folder_path)
        folder_obj = create_entry(
            self.context.volume,
            self.context.root_file,
            folder_path,
        )

        folder_r_name = "example2"
        folder_r_path = os.path.join(self.context.root_path, folder_r_name)
        rename_file(self.context.admin, folder_obj.id, folder_r_name)
        folder_obj.refresh_from_db()
        self.assertEqual(folder_r_name, folder_obj.name)
        self.assertEqual(f"/{folder_r_name}", folder_obj.path_from_vol)
        self.assertTrue(os.path.exists(folder_r_path))
        self.assertFalse(os.path.exists(folder_path))

    def test_rename_file_2(self):
        """Test rename_file (Same name)"""
        folder_name = "example"
        folder_path = os.path.join(self.context.root_path, folder_name)
        os.makedirs(folder_path)
        folder_obj = create_entry(
            self.context.volume,
            self.context.root_file,
            folder_path,
        )
        rename_file(self.context.admin, folder_obj.id, folder_name)
        folder_obj.refresh_from_db()
        self.assertEqual(folder_name, folder_obj.name)

    def test_rename_file_3(self):
        """Test rename_file (Empty name)"""
        folder_name = "example"
        folder_path = os.path.join(self.context.root_path, folder_name)
        os.makedirs(folder_path)
        folder_obj = create_entry(
            self.context.volume,
            self.context.root_file,
            folder_path,
        )

        # None name
        with self.assertRaises(InvalidFileNameException):
            rename_file(self.context.admin, folder_obj.id, None)
        folder_obj.refresh_from_db()
        self.assertEqual(folder_name, folder_obj.name)

        # No name
        with self.assertRaises(InvalidFileNameException):
            rename_file(self.context.admin, folder_obj.id, "")
        folder_obj.refresh_from_db()
        self.assertEqual(folder_name, folder_obj.name)

        # Useless name
        with self.assertRaises(InvalidFileNameException):
            rename_file(self.context.admin, folder_obj.id, "  \n")
        folder_obj.refresh_from_db()
        self.assertEqual(folder_name, folder_obj.name)

    def test_rename_file_4(self):
        """Test rename_file (Same name with sibling)"""
        folder_1_name = "example"
        folder_1_path = os.path.join(self.context.root_path, folder_1_name)
        os.makedirs(folder_1_path)
        folder_1_obj = create_entry(
            self.context.volume,
            self.context.root_file,
            folder_1_path,
        )

        folder_2_name = "example2"
        folder_2_path = os.path.join(self.context.root_path, folder_2_name)
        os.makedirs(folder_2_path)
        create_entry(
            self.context.volume,
            self.context.root_file,
            folder_2_path,
        )

        with self.assertRaises(InvalidFileNameException):
            rename_file(self.context.admin, folder_1_obj.id, folder_2_name)
        folder_1_obj.refresh_from_db()
        self.assertEqual(folder_1_name, folder_1_obj.name)

    def test_rename_file_5(self):
        """Test rename_file (Above parent)"""
        folder_name = "example"
        folder_path = os.path.join(self.context.root_path, folder_name)
        os.makedirs(folder_path)
        folder_obj = create_entry(
            self.context.volume,
            self.context.root_file,
            folder_path,
        )

        with self.assertRaises(InvalidFileNameException):
            rename_file(self.context.admin, folder_obj.id, "../../example")
        folder_obj.refresh_from_db()
        self.assertEqual(folder_name, folder_obj.name)

    def test_rename_file_6(self):
        """Test rename_file (Deeper path)"""
        folder_name = "example"
        folder_path = os.path.join(self.context.root_path, folder_name)
        os.makedirs(folder_path)
        folder_obj = create_entry(
            self.context.volume,
            self.context.root_file,
            folder_path,
        )

        with self.assertRaises(InvalidFileNameException):
            rename_file(self.context.admin, folder_obj.id, "gg/gg")
        folder_obj.refresh_from_db()
        self.assertEqual(folder_name, folder_obj.name)

    def test_rename_file_7(self):
        """Test rename_file (Root dir)"""
        with self.assertRaises(InvalidOperationRequestException):
            rename_file(self.context.admin, self.context.root_file.id, "example")
        self.context.root_file.refresh_from_db()
        self.assertEqual("", self.context.root_file.name)

    def test_rename_file_8(self):
        """Test rename_file (Remote path)"""
        folder_name = "example"
        folder_path = os.path.join(self.context.root_path, folder_name)
        os.makedirs(folder_path)
        folder_obj = create_entry(
            self.context.volume,
            self.context.root_file,
            folder_path,
        )

        self.context.volume.kind = VolumeKindEnum.REMOTE_RPI_DRIVE
        self.context.volume.save()

        with self.assertRaises(NotImplementedError):
            rename_file(self.context.admin, folder_obj.id, "example2")
        folder_obj.refresh_from_db()
        self.assertEqual(folder_name, folder_obj.name)

    def test_rename_file_9(self):
        """Test rename_file (No role user)"""
        folder_name = "example"
        folder_path = os.path.join(self.context.root_path, folder_name)
        os.makedirs(folder_path)
        folder_obj = create_entry(
            self.context.volume,
            self.context.root_file,
            folder_path,
        )

        normal_user = User.objects.create_user("normal")

        with self.assertRaises(FileNotFoundException):
            rename_file(normal_user, folder_obj.id, "example2")
        folder_obj.refresh_from_db()
        self.assertEqual(folder_name, folder_obj.name)
        self.assertTrue(os.path.exists(folder_path))

    def test_rename_file_10(self):
        """Test rename_file (Read-only user)"""
        folder_name = "example"
        folder_path = os.path.join(self.context.root_path, folder_name)
        os.makedirs(folder_path)
        folder_obj = create_entry(
            self.context.volume,
            self.context.root_file,
            folder_path,
        )

        normal_user = User.objects.create_user("normal")
        update_volume_permission(
            self.context.admin,
            self.context.volume.id,
            [
                VolumePermissionModel(
                    user=normal_user.id,
                    permission=VolumePermissionEnum.READ,
                )
            ],
        )

        with self.assertRaises(NoPermissionException):
            rename_file(normal_user, folder_obj.id, "example2")
        folder_obj.refresh_from_db()
        self.assertEqual(folder_name, folder_obj.name)
        self.assertTrue(os.path.exists(folder_path))

    def test_rename_file_11(self):
        """Test rename_file (Read-write user)"""
        folder_name = "example"
        folder_path = os.path.join(self.context.root_path, folder_name)
        os.makedirs(folder_path)
        folder_obj = create_entry(
            self.context.volume,
            self.context.root_file,
            folder_path,
        )

        folder_r_name = "example2"
        folder_r_path = os.path.join(self.context.root_path, folder_r_name)

        normal_user = User.objects.create_user("normal")
        update_volume_permission(
            self.context.admin,
            self.context.volume.id,
            [
                VolumePermissionModel(
                    user=normal_user.id,
                    permission=VolumePermissionEnum.READ_WRITE,
                )
            ],
        )

        rename_file(normal_user, folder_obj.id, folder_r_name)
        folder_obj.refresh_from_db()
        self.assertEqual(folder_r_name, folder_obj.name)
        self.assertFalse(os.path.exists(folder_path))
        self.assertTrue(os.path.exists(folder_r_path))

    def test_rename_file_12(self):
        """Test rename_file (Non-existence file)"""
        with self.assertRaises(FileNotFoundException):
            rename_file(self.context.admin, str(uuid.uuid4()), "blahblah")

    def test_compress_files_1(self):
        """Test compress_files"""
        text_fp = os.path.join(self.context.root_path, "hehe.txt")
        with open(text_fp, "w+") as f_h:
            f_h.write("a")
        txt_file = create_entry(self.context.volume, self.context.root_file, text_fp)

        zip_name = "hehe.zip"
        job = compress_files(
            self.context.admin,
            [str(txt_file.id)],
            str(self.context.root_file.id),
            zip_name,
        )
        self.assertIsNotNone(job)
        self.assertEqual(JobKind.ZIP, job.kind)
        self.assertEqual(self.context.volume.id, job.volume_id)
        self.assertEqual(
            {
                "files": [str(txt_file.id)],
                "parent": str(self.context.root_file.id),
                "name": zip_name,
            },
            job.data,
        )

    def test_compress_files_2(self):
        """Test compress_files (Invalid name)"""
        text_fp = os.path.join(self.context.root_path, "hehe.txt")
        with open(text_fp, "w+") as f_h:
            f_h.write("a")
        txt_file = create_entry(self.context.volume, self.context.root_file, text_fp)

        zip_names = [None, "", " "]
        for zip_name in zip_names:
            with self.assertRaises(InvalidFileNameException):
                compress_files(
                    self.context.admin,
                    [str(txt_file.id)],
                    str(self.context.root_file.id),
                    zip_name,
                )

    def test_compress_files_3(self):
        """Test compress_files (Auto add .zip to name)"""
        text_fp = os.path.join(self.context.root_path, "hehe.txt")
        with open(text_fp, "w+") as f_h:
            f_h.write("a")
        txt_file = create_entry(self.context.volume, self.context.root_file, text_fp)

        zip_name = "hehe"
        job = compress_files(
            self.context.admin,
            [str(txt_file.id)],
            str(self.context.root_file.id),
            zip_name,
        )
        self.assertIsNotNone(job)
        self.assertEqual(JobKind.ZIP, job.kind)
        self.assertEqual(self.context.volume.id, job.volume_id)
        self.assertEqual(
            {
                "files": [str(txt_file.id)],
                "parent": str(self.context.root_file.id),
                "name": f"{zip_name}.zip",
            },
            job.data,
        )

    def test_compress_files_4(self):
        """Test compress_files (No file)"""
        with self.assertRaises(InvalidOperationRequestException) as error:
            compress_files(
                self.context.admin,
                [],
                str(self.context.root_file.id),
                "gg.zip",
            )
        self.assertEqual(str(error.exception), "No file to compress.")

    def test_compress_files_5(self):
        """Test compress_files (Invalid file id)"""
        with self.assertRaises(InvalidOperationRequestException) as error:
            compress_files(
                self.context.admin,
                [str(uuid.uuid4())],
                str(self.context.root_file.id),
                "gg.zip",
            )
        self.assertEqual(str(error.exception), "Invalid file to compress.")

    def test_compress_files_6(self):
        """Test compress_files (Files from different volume)"""
        text_fp_1 = os.path.join(self.context.root_path, "hehe.txt")
        with open(text_fp_1, "w+") as f_h:
            f_h.write("a")
        txt_file_1 = create_entry(
            self.context.volume, self.context.root_file, text_fp_1
        )

        self.context_2 = SetupContext()
        text_fp_2 = os.path.join(self.context_2.root_path, "file2.txt")
        with open(text_fp_2, "w+") as f_h:
            f_h.write("a")
        txt_file_2 = create_entry(
            self.context_2.volume, self.context_2.root_file, text_fp_2
        )

        with self.assertRaises(InvalidOperationRequestException) as error:
            compress_files(
                self.context.admin,
                [str(txt_file_1.id), str(txt_file_2.id)],
                str(self.context.root_file.id),
                "gg.zip",
            )
        self.assertEqual(
            str(error.exception), "Files & destination must be in the same volume."
        )

    def test_compress_files_7(self):
        """Test compress_files (Destination in different volume)"""
        text_fp_1 = os.path.join(self.context.root_path, "hehe.txt")
        with open(text_fp_1, "w+") as f_h:
            f_h.write("a")
        txt_file_1 = create_entry(
            self.context.volume, self.context.root_file, text_fp_1
        )

        self.context_2 = SetupContext()

        with self.assertRaises(InvalidOperationRequestException) as error:
            compress_files(
                self.context.admin,
                [str(txt_file_1.id)],
                str(self.context_2.root_file.id),
                "gg.zip",
            )
        self.assertEqual(
            str(error.exception), "Files & destination must be in the same volume."
        )

    def test_compress_files_8(self):
        """Test compress_files (Destination is file)"""
        text_fp_1 = os.path.join(self.context.root_path, "hehe.txt")
        with open(text_fp_1, "w+") as f_h:
            f_h.write("a")
        txt_file_1 = create_entry(
            self.context.volume, self.context.root_file, text_fp_1
        )

        text_fp_2 = os.path.join(self.context.root_path, "hehe2.txt")
        with open(text_fp_2, "w+") as f_h:
            f_h.write("a")
        txt_file_2 = create_entry(
            self.context.volume, self.context.root_file, text_fp_2
        )

        with self.assertRaises(InvalidOperationRequestException) as error:
            compress_files(
                self.context.admin,
                [str(txt_file_1.id)],
                str(txt_file_2.id),
                "gg.zip",
            )
        self.assertEqual(str(error.exception), "Can't create zip file in a file.")

    def test_compress_files_9(self):
        """Test compress_files (Files on different level)"""
        text_fp_1 = os.path.join(self.context.root_path, "hehe.txt")
        with open(text_fp_1, "w+") as f_h:
            f_h.write("a")
        txt_file_1 = create_entry(
            self.context.volume, self.context.root_file, text_fp_1
        )

        with self.assertRaises(InvalidOperationRequestException) as error:
            compress_files(
                self.context.admin,
                [str(txt_file_1.id), str(self.context.root_file.id)],
                str(self.context.root_file.id),
                "gg.zip",
            )
        self.assertEqual(
            str(error.exception), "Only can compress items in the same level!"
        )

    def test_compress_files_10(self):
        """Test compress_files (Permission)"""
        text_fp = os.path.join(self.context.root_path, "hehe.txt")
        with open(text_fp, "w+") as f_h:
            f_h.write("a")
        txt_file = create_entry(self.context.volume, self.context.root_file, text_fp)

        zip_name = "hehe.zip"
        roles = [VolumePermissionEnum.NONE, VolumePermissionEnum.READ]
        excs = [VolumeNotFoundException, NoPermissionException]
        normal_user = User.objects.create_user("normal_user")

        for idx, role in enumerate(roles):
            update_volume_permission(
                self.context.admin,
                self.context.volume.id,
                (
                    [
                        VolumePermissionModel(
                            user=normal_user.id,
                            permission=role,
                        )
                    ]
                    if roles
                    else []
                ),
            )
            with self.assertRaises(excs[idx]):
                compress_files(
                    normal_user,
                    [str(txt_file.id)],
                    str(self.context.root_file.id),
                    zip_name,
                )

        roles = [VolumePermissionEnum.READ_WRITE, VolumePermissionEnum.ADMIN]
        for role in roles:
            update_volume_permission(
                self.context.admin,
                self.context.volume.id,
                [
                    VolumePermissionModel(
                        user=normal_user.id,
                        permission=role,
                    )
                ],
            )
            job = compress_files(
                normal_user,
                [str(txt_file.id)],
                str(self.context.root_file.id),
                zip_name,
            )
            self.assertIsNotNone(job)

    def test_compress_files_11(self):
        """Test compress_files (Remote path)"""
        text_fp = os.path.join(self.context.root_path, "hehe.txt")
        with open(text_fp, "w+") as f_h:
            f_h.write("a")
        txt_file = create_entry(self.context.volume, self.context.root_file, text_fp)

        self.context.volume.kind = VolumeKindEnum.REMOTE_RPI_DRIVE
        self.context.volume.save()

        with self.assertRaises(NotImplementedError):
            compress_files(
                self.context.admin,
                [str(txt_file.id)],
                str(self.context.root_file.id),
                "hehe.zip",
            )

    def test_move_files_1(self):
        """Test move files"""
        text_fp = os.path.join(self.context.root_path, "hehe.txt")
        with open(text_fp, "w+") as f_h:
            f_h.write("a")
        txt_file = create_entry(self.context.volume, self.context.root_file, text_fp)

        folder_fp = os.path.join(self.context.root_path, "example")
        os.makedirs(folder_fp)
        folder_obj = create_entry(
            self.context.volume, self.context.root_file, folder_fp
        )

        move_files(self.context.admin, [str(txt_file.id)], str(folder_obj.id), False)
        txt_file.refresh_from_db()
        self.assertEqual("/example/hehe.txt", txt_file.path_from_vol)
        self.assertFalse(os.path.exists(text_fp))
        self.assertTrue(os.path.join(folder_fp, "hehe.txt"))

    def test_move_files_2(self):
        """Test move files (Rename on conflict)"""
        text_fp = os.path.join(self.context.root_path, "hehe.txt")
        with open(text_fp, "w+") as f_h:
            f_h.write("a")
        txt_file = create_entry(self.context.volume, self.context.root_file, text_fp)

        folder_fp = os.path.join(self.context.root_path, "example")
        os.makedirs(folder_fp)
        folder_obj = create_entry(
            self.context.volume, self.context.root_file, folder_fp
        )
        text_fp_2 = os.path.join(folder_fp, "hehe.txt")
        with open(text_fp_2, "w+") as f_h:
            f_h.write("a")
        txt_file_2 = create_entry(self.context.volume, folder_obj, text_fp_2)

        move_files(self.context.admin, [str(txt_file.id)], str(folder_obj.id), True)

        txt_file.refresh_from_db()
        self.assertFalse(os.path.exists(text_fp))
        self.assertTrue(os.path.exists(os.path.join(folder_fp, "hehe (1).txt")))
        self.assertEqual("hehe (1).txt", txt_file.name)
        self.assertEqual("/example/hehe (1).txt", txt_file.path_from_vol)

        txt_file_2.refresh_from_db()
        self.assertTrue(os.path.exists(text_fp_2))
        self.assertTrue(os.path.exists(os.path.join(folder_fp, "hehe.txt")))
        self.assertEqual("hehe.txt", txt_file_2.name)
        self.assertEqual("/example/hehe.txt", txt_file_2.path_from_vol)

    def test_move_files_3(self):
        """Test move files (Replace on conflict)"""
        text_fp = os.path.join(self.context.root_path, "hehe.txt")
        with open(text_fp, "w+") as f_h:
            f_h.write("a")
        txt_file = create_entry(self.context.volume, self.context.root_file, text_fp)

        folder_fp = os.path.join(self.context.root_path, "example")
        os.makedirs(folder_fp)
        folder_obj = create_entry(
            self.context.volume, self.context.root_file, folder_fp
        )
        text_fp_2 = os.path.join(folder_fp, "hehe.txt")
        with open(text_fp_2, "w+") as f_h:
            f_h.write("b")
        txt_file_2 = create_entry(self.context.volume, folder_obj, text_fp_2)

        move_files(self.context.admin, [str(txt_file.id)], str(folder_obj.id), False)

        txt_file.refresh_from_db()
        self.assertFalse(os.path.exists(text_fp))
        self.assertTrue(os.path.exists(text_fp_2))
        self.assertEqual("hehe.txt", txt_file.name)
        self.assertEqual("/example/hehe.txt", txt_file.path_from_vol)
        with open(text_fp_2, "r") as f_h:
            self.assertEqual("a", f_h.read())

        self.assertFalse(File.objects.filter(id=txt_file_2.id).exists())

    def test_move_files_4(self):
        """Test move files (No role / Read only)"""
        text_fp = os.path.join(self.context.root_path, "hehe.txt")
        with open(text_fp, "w+") as f_h:
            f_h.write("a")
        txt_file = create_entry(self.context.volume, self.context.root_file, text_fp)

        folder_fp = os.path.join(self.context.root_path, "example")
        os.makedirs(folder_fp)
        folder_obj = create_entry(
            self.context.volume, self.context.root_file, folder_fp
        )

        normal_user = User.objects.create_user("normal")
        roles = [VolumePermissionEnum.NONE, VolumePermissionEnum.READ]
        exc = [FileNotFoundException, NoPermissionException]

        for idx, role in enumerate(roles):
            update_volume_permission(
                self.context.admin,
                self.context.volume.id,
                (
                    [
                        VolumePermissionModel(
                            user=normal_user.id,
                            permission=role,
                        )
                    ]
                    if roles
                    else []
                ),
            )
            with self.assertRaises(exc[idx]):
                move_files(normal_user, [str(txt_file.id)], str(folder_obj.id), False)
            txt_file.refresh_from_db()
            self.assertEqual("/hehe.txt", txt_file.path_from_vol)
            self.assertTrue(os.path.exists(text_fp))
            self.assertFalse(os.path.exists(os.path.join(folder_fp, "hehe.txt")))

    def test_move_files_5(self):
        """Test move files (Read-Write user)"""
        text_fp = os.path.join(self.context.root_path, "hehe.txt")
        with open(text_fp, "w+") as f_h:
            f_h.write("a")
        txt_file = create_entry(self.context.volume, self.context.root_file, text_fp)

        folder_fp = os.path.join(self.context.root_path, "example")
        os.makedirs(folder_fp)
        folder_obj = create_entry(
            self.context.volume, self.context.root_file, folder_fp
        )

        normal_user = User.objects.create_user("normal")
        update_volume_permission(
            self.context.admin,
            self.context.volume.id,
            [
                VolumePermissionModel(
                    user=normal_user.id,
                    permission=VolumePermissionEnum.READ_WRITE,
                )
            ],
        )
        move_files(normal_user, [str(txt_file.id)], str(folder_obj.id), False)
        txt_file.refresh_from_db()
        self.assertEqual("/example/hehe.txt", txt_file.path_from_vol)
        self.assertFalse(os.path.exists(text_fp))
        self.assertTrue(os.path.join(folder_fp, "hehe.txt"))

    def test_move_files_6(self):
        """Test move files (Volume admin user)"""
        text_fp = os.path.join(self.context.root_path, "hehe.txt")
        with open(text_fp, "w+") as f_h:
            f_h.write("a")
        txt_file = create_entry(self.context.volume, self.context.root_file, text_fp)

        folder_fp = os.path.join(self.context.root_path, "example")
        os.makedirs(folder_fp)
        folder_obj = create_entry(
            self.context.volume, self.context.root_file, folder_fp
        )

        normal_user = User.objects.create_user("normal")
        update_volume_permission(
            self.context.admin,
            self.context.volume.id,
            [
                VolumePermissionModel(
                    user=normal_user.id,
                    permission=VolumePermissionEnum.ADMIN,
                )
            ],
        )
        move_files(normal_user, [str(txt_file.id)], str(folder_obj.id), False)
        txt_file.refresh_from_db()
        self.assertEqual("/example/hehe.txt", txt_file.path_from_vol)
        self.assertFalse(os.path.exists(text_fp))
        self.assertTrue(os.path.join(folder_fp, "hehe.txt"))

    def test_move_files_7(self):
        """Test move files (No file)"""
        folder_fp = os.path.join(self.context.root_path, "example")
        os.makedirs(folder_fp)
        folder_obj = create_entry(
            self.context.volume, self.context.root_file, folder_fp
        )
        with self.assertRaises(InvalidOperationRequestException) as error:
            move_files(self.context.admin, [], str(folder_obj.id), False)
        self.assertEqual("No file to move.", str(error.exception))

    def test_move_files_8(self):
        """Test move files (Invalid file)"""
        folder_fp = os.path.join(self.context.root_path, "example")
        os.makedirs(folder_fp)
        folder_obj = create_entry(
            self.context.volume, self.context.root_file, folder_fp
        )
        with self.assertRaises(InvalidOperationRequestException) as error:
            move_files(
                self.context.admin, [str(uuid.uuid4())], str(folder_obj.id), False
            )
        self.assertEqual("No file to move.", str(error.exception))

    def test_move_files_9(self):
        """Test move files (Files from different volumes)"""
        text_fp_1 = os.path.join(self.context.root_path, "hehe.txt")
        with open(text_fp_1, "w+") as f_h:
            f_h.write("a")
        txt_file_1 = create_entry(
            self.context.volume, self.context.root_file, text_fp_1
        )

        self.context_2 = SetupContext()
        text_fp_2 = os.path.join(self.context_2.root_path, "file2.txt")
        with open(text_fp_2, "w+") as f_h:
            f_h.write("a")
        txt_file_2 = create_entry(
            self.context_2.volume, self.context_2.root_file, text_fp_2
        )

        folder_fp = os.path.join(self.context.root_path, "example")
        os.makedirs(folder_fp)
        folder_obj = create_entry(
            self.context.volume, self.context.root_file, folder_fp
        )
        with self.assertRaises(InvalidOperationRequestException) as error:
            move_files(
                self.context.admin,
                [str(txt_file_1.id), str(txt_file_2.id)],
                str(folder_obj.id),
                False,
            )
        self.assertEqual("Files must be from the same volume.", str(error.exception))

    def test_move_files_10(self):
        """Test move files (Remote)"""
        text_fp = os.path.join(self.context.root_path, "hehe.txt")
        with open(text_fp, "w+") as f_h:
            f_h.write("a")
        txt_file = create_entry(self.context.volume, self.context.root_file, text_fp)

        self.context.volume.kind = VolumeKindEnum.REMOTE_RPI_DRIVE
        self.context.volume.save()

        with self.assertRaises(NotImplementedError):
            move_files(
                self.context.admin,
                [str(txt_file.id)],
                str(self.context.root_file.id),
                False,
            )

    def test_share_file_1(self):
        """Test share_file"""
        text_fp = os.path.join(self.context.root_path, "hehe.txt")
        with open(text_fp, "w+") as f_h:
            f_h.write("a")
        txt_file = create_entry(self.context.volume, self.context.root_file, text_fp)

        link = share_file(self.context.admin, txt_file.id)
        self.assertEqual(txt_file, link.file)
        self.assertEqual(self.context.admin, link.creator)
        self.assertEqual(
            timedelta(
                minutes=settings.ROOT_CONFIG.web.public_link_expiry
            ).total_seconds(),
            round((link.expire_time - timezone.now()).total_seconds()),
        )

    def test_share_file_2(self):
        """Test share_file (Invalid file id)"""
        with self.assertRaises(FileNotFoundException):
            share_file(self.context.admin, str(uuid.uuid4()))

    def test_share_file_3(self):
        """Test share_file (No permission)"""
        text_fp = os.path.join(self.context.root_path, "hehe.txt")
        with open(text_fp, "w+") as f_h:
            f_h.write("a")
        txt_file = create_entry(self.context.volume, self.context.root_file, text_fp)

        normal_user = User.objects.create_user("normal")
        with self.assertRaises(FileNotFoundException):
            share_file(normal_user, str(txt_file.id))

    def test_share_file_4(self):
        """Test share_file (Read-only user)"""
        text_fp = os.path.join(self.context.root_path, "hehe.txt")
        with open(text_fp, "w+") as f_h:
            f_h.write("a")
        txt_file = create_entry(self.context.volume, self.context.root_file, text_fp)

        normal_user = User.objects.create_user("normal")
        update_volume_permission(
            self.context.admin,
            self.context.volume.id,
            [
                VolumePermissionModel(
                    user=normal_user.id,
                    permission=VolumePermissionEnum.READ,
                )
            ],
        )
        share_file(normal_user, str(txt_file.id))

    def test_share_file_5(self):
        """Test share_file (Folder)"""
        folder_fp = os.path.join(self.context.root_path, "hehe")
        os.makedirs(folder_fp)
        folder_obj = create_entry(
            self.context.volume, self.context.root_file, folder_fp
        )

        with self.assertRaises(InvalidOperationRequestException) as error:
            share_file(self.context.admin, str(folder_obj.id))
        self.assertEqual("Can't share folder.", str(error.exception))

    def test_create_folder_1(self):
        """Test create_folder"""
        folder_obj = create_folder(
            self.context.admin, self.context.root_file.id, "fold"
        )
        self.assertIsNotNone(folder_obj)
        self.assertEqual("fold", folder_obj.name)
        self.assertEqual("/fold", folder_obj.path_from_vol)
        self.assertTrue(os.path.isdir(os.path.join(self.context.root_path, "fold")))

    def test_create_folder_2(self):
        """Test create folder (No role)"""
        normal_user = User.objects.create_user("normal")
        with self.assertRaises(FileNotFoundException):
            create_folder(normal_user, self.context.root_file.id, "fold")

    def test_create_folder_3(self):
        """Test create folder (Read-only user)"""
        normal_user = User.objects.create_user("normal")
        update_volume_permission(
            self.context.admin,
            self.context.volume.id,
            [
                VolumePermissionModel(
                    user=normal_user.pk, permission=VolumePermissionEnum.READ
                )
            ],
        )
        with self.assertRaises(NoPermissionException):
            create_folder(normal_user, self.context.root_file.id, "fold")

    def test_create_folder_4(self):
        """Test create folder (Read-write user)"""
        normal_user = User.objects.create_user("normal")
        update_volume_permission(
            self.context.admin,
            self.context.volume.id,
            [
                VolumePermissionModel(
                    user=normal_user.pk, permission=VolumePermissionEnum.READ_WRITE
                )
            ],
        )
        folder_obj = create_folder(
            self.context.admin, self.context.root_file.id, "fold"
        )
        self.assertIsNotNone(folder_obj)
        self.assertEqual("fold", folder_obj.name)
        self.assertEqual("/fold", folder_obj.path_from_vol)
        self.assertTrue(os.path.isdir(os.path.join(self.context.root_path, "fold")))

    def test_create_folder_5(self):
        """Test create_folder (Invalid parent)"""
        with self.assertRaises(FileNotFoundException):
            create_folder(self.context.admin, str(uuid.uuid4()), "fold")

    def test_create_folder_6(self):
        """Test create_folder (Parent is file)"""
        text_fp = os.path.join(self.context.root_path, "hehe.txt")
        with open(text_fp, "w+") as f_h:
            f_h.write("a")
        txt_file = create_entry(self.context.volume, self.context.root_file, text_fp)

        with self.assertRaises(InvalidOperationRequestException) as error:
            create_folder(self.context.admin, txt_file.id, "fold")
        self.assertEqual("Can't create folder in file.", str(error.exception))

    def test_create_folder_7(self):
        """Test create_folder (Null name)"""
        with self.assertRaises(InvalidFileNameException):
            create_folder(self.context.admin, self.context.root_file.id, None)

    def test_create_folder_8(self):
        """Test create_folder (Invalid name)"""
        with self.assertRaises(InvalidFileNameException):
            create_folder(self.context.admin, self.context.root_file.id, "")

        with self.assertRaises(InvalidFileNameException):
            create_folder(self.context.admin, self.context.root_file.id, "  ")

    def test_create_folder_9(self):
        """Test create_folder (Remote volume)"""
        self.context.volume.kind = VolumeKindEnum.REMOTE_RPI_DRIVE
        self.context.volume.save()

        with self.assertRaises(NotImplementedError):
            create_folder(self.context.admin, self.context.root_file.id, "gg")

    def test_search_files(self):
        """Test search_files"""
        text_fp_1 = os.path.join(self.context.root_path, "hehe.txt")
        with open(text_fp_1, "w+") as f_h:
            f_h.write("a")
        txt_file_1 = create_entry(
            self.context.volume, self.context.root_file, text_fp_1
        )

        self.context_2 = SetupContext()
        text_fp_2 = os.path.join(self.context_2.root_path, "file2.txt")
        with open(text_fp_2, "w+") as f_h:
            f_h.write("a")
        txt_file_2 = create_entry(
            self.context_2.volume, self.context_2.root_file, text_fp_2
        )

        result = set(search_files(self.context.admin, "txt").all())
        self.assertEqual({txt_file_1, txt_file_2}, result)

        normal_user = User.objects.create_user("normal")
        update_volume_permission(
            self.context_2.admin,
            self.context_2.volume.id,
            [
                VolumePermissionModel(
                    user=normal_user.pk, permission=VolumePermissionEnum.READ
                )
            ],
        )

        result = set(search_files(normal_user, "txt").all())
        self.assertEqual({txt_file_2}, result)

    def test_get_file_full_path_1(self):
        """Test get_file_full_path"""
        self.assertEqual(
            self.context.root_path, get_file_full_path(self.context.root_file)
        )

        text_fp = os.path.join(self.context.root_path, "hehe.txt")
        with open(text_fp, "w+") as f_h:
            f_h.write("a")
        txt_file = create_entry(self.context.volume, self.context.root_file, text_fp)
        self.assertEqual(text_fp, get_file_full_path(txt_file))

    def test_get_file_full_path_2(self):
        """Test get_file_full_path (Remote path)"""
        self.context.volume.kind = VolumeKindEnum.REMOTE_RPI_DRIVE
        self.context.volume.save()

        with self.assertRaises(NotImplementedError):
            get_file_full_path(self.context.root_file)
