import os
import shutil

from zipfile import ZipFile

from django.contrib.auth.models import User
from django.db import transaction
from django.test import TestCase

from rpidrive.controllers.compress import NoFileException
from rpidrive.controllers.local_file import (
    InvalidFileNameException,
    InvalidOperationRequestException,
    InvalidVolumeKindException,
    compress_files,
    create_entry,
    create_folder,
    delete_file,
    generate_new_file_name,
    get_file_parents,
    get_full_path,
    get_metadata,
    move_files,
    perform_index,
    process_compress_job,
    rename_file,
)
from rpidrive.models import (
    File,
    FileKindEnum,
    Job,
    JobStatus,
    VolumeKindEnum,
)
from rpidrive.tests.helpers.setup import SetupContext


class TestLocalFileController(TestCase):  # pylint: disable=too-many-public-methods
    """Test local_file controller"""

    def setUp(self):
        self.context = SetupContext()

    def tearDown(self):
        self.context.cleanup()
        Job.objects.all().delete()
        User.objects.all().delete()

    def test_generate_new_file_name(self):
        """Test generate_new_file_name"""
        test_data = [
            ("New Folder", {}, "New Folder"),
            ("New Folder", {"New Folder"}, "New Folder (1)"),
            ("New Folder", {"New Folder", "New Folder (1)"}, "New Folder (2)"),
            ("1.mp4", {}, "1.mp4"),
            ("1.mp4", {"1.mp4"}, "1 (1).mp4"),
            ("1.mp4", {"1 (1).mp4"}, "1.mp4"),
        ]
        for data in test_data:
            self.assertEqual(data[2], generate_new_file_name(data[0], data[1]))

    def test_get_full_path_1(self):
        """Test get_full_path"""
        folder_name = "example"
        folder_path = os.path.join(self.context.root_path, folder_name)
        os.makedirs(folder_path)
        folder_obj = create_entry(
            self.context.volume,
            self.context.root_file,
            folder_path,
        )

        file_1 = "log.txt"
        file_path = os.path.join(self.context.root_path, folder_name, file_1)
        with open(file_path, "w+") as f_h:
            f_h.write("")
        file_obj = create_entry(
            self.context.volume,
            self.context.root_file,
            file_path,
        )

        self.assertEqual(self.context.root_path, get_full_path(self.context.root_file))
        self.assertEqual(folder_path, get_full_path(folder_obj))
        self.assertEqual(file_path, get_full_path(file_obj))

    def test_get_metadata_1(self):
        """Test get_metadata (Folder)"""
        folder_name = "example"
        folder_path = os.path.join(self.context.root_path, folder_name)
        os.makedirs(folder_path)
        self.assertIsNone(get_metadata(folder_path))

    def test_get_metadata_2(self):
        """Test get_metadata (Empty file)"""
        file = "log.txt"
        file_path = os.path.join(self.context.root_path, file)
        with open(file_path, "w+") as f_h:
            f_h.write("")
        self.assertIsNone(get_metadata(file_path))

    def test_get_metadata_3(self):
        """Test get_metadata (Invalid pdf)"""
        file = "log.pdf"
        file_path = os.path.join(self.context.root_path, file)
        with open(file_path, "w+") as f_h:
            f_h.write("")
        self.assertIsNone(get_metadata(file_path))

    def test_get_metadata_4(self):
        """Test get_metadata (Audio)"""
        file_path = os.path.join(
            os.path.dirname(os.path.realpath(__file__)), "sample.m4a"
        )
        data = get_metadata(file_path)
        self.assertEqual("anya", data["album"])
        self.assertEqual("ice cream", data["artist"])
        self.assertEqual("lollipop", data["title"])

    def test_get_metadata_5(self):
        """Test get_metadata (Image)"""
        file_path = os.path.join(
            os.path.dirname(os.path.realpath(__file__)), "sample.jpg"
        )
        data = get_metadata(file_path)
        self.assertEqual("Canon", data["Image Make"])
        self.assertEqual("Canon EOS 40D", data["Image Model"])

    def test_perform_index_1(self):
        """Test perform_index (All new)"""
        folder_name = "example"
        folder_path = os.path.join(self.context.root_path, folder_name)
        os.makedirs(folder_path)

        file_name = "sample.m4a"
        src_file = os.path.join(
            os.path.dirname(os.path.realpath(__file__)), "sample.m4a"
        )
        file_path = os.path.join(self.context.root_path, folder_name, file_name)
        shutil.copy2(src_file, file_path)

        with transaction.atomic():
            perform_index(self.context.volume)

        file_list = File.objects.all()
        folder_obj = None
        file_obj = None
        for file in file_list:
            if file == self.context.root_file:
                continue
            if file.name not in {folder_name, file_name}:
                self.fail("Unknown file.")
            if file.name == folder_name:
                folder_obj = file
            elif file.name == file_name:
                file_obj = file
        self.assertIsNotNone(folder_obj)
        self.assertEqual(
            {
                "name": folder_name,
                "kind": "folder",
                "parent_id": self.context.root_file.id,
                "volume_id": self.context.volume.id,
                "path_from_vol": f"/{folder_name}",
                "media_type": None,
                "size": 4096,
                "metadata": None,
            },
            {
                "name": folder_obj.name,
                "kind": folder_obj.kind,
                "parent_id": folder_obj.parent_id,
                "volume_id": folder_obj.volume_id,
                "path_from_vol": folder_obj.path_from_vol,
                "media_type": folder_obj.media_type,
                "size": folder_obj.size,
                "metadata": folder_obj.metadata,
            },
        )
        self.assertIsNotNone(folder_obj.last_modified)
        self.assertIsNotNone(file_obj)
        self.assertEqual(
            {
                "name": file_name,
                "kind": "file",
                "parent_id": folder_obj.id,
                "volume_id": self.context.volume.id,
                "path_from_vol": f"/{folder_name}/{file_name}",
                "media_type": "audio/mp4",
                "size": 260492,
            },
            {
                "name": file_obj.name,
                "kind": file_obj.kind,
                "parent_id": file_obj.parent_id,
                "volume_id": file_obj.volume_id,
                "path_from_vol": file_obj.path_from_vol,
                "media_type": file_obj.media_type,
                "size": file_obj.size,
            },
        )
        self.assertEqual("anya", file_obj.metadata["album"])
        self.assertEqual("ice cream", file_obj.metadata["artist"])
        self.assertEqual("lollipop", file_obj.metadata["title"])
        self.assertIsNotNone(file_obj.last_modified)

    def test_perform_index_2(self):
        """Test perform_index (Patch)"""
        folder_name = "example"
        folder_path = os.path.join(self.context.root_path, folder_name)
        os.makedirs(folder_path)

        file_name = "sample.m4a"
        src_file = os.path.join(os.path.dirname(os.path.realpath(__file__)), file_name)
        file_path = os.path.join(self.context.root_path, folder_name, file_name)
        shutil.copy2(src_file, file_path)

        with transaction.atomic():
            perform_index(self.context.volume)

        self.assertEqual(3, File.objects.count())

        shutil.rmtree(folder_path)
        file_name_2 = "sample.jpg"
        src_file = os.path.join(
            os.path.dirname(os.path.realpath(__file__)), file_name_2
        )
        file_path = os.path.join(self.context.root_path, file_name_2)
        shutil.copy2(src_file, file_path)

        # Test addition & removal
        with transaction.atomic():
            perform_index(self.context.volume)
        files = File.objects.all()
        self.assertEqual(2, files.count())
        for file in files:
            if file == self.context.root_file:
                continue
            self.assertEqual(
                {
                    "name": file_name_2,
                    "kind": "file",
                    "parent_id": self.context.root_file.id,
                    "volume_id": self.context.volume.id,
                    "path_from_vol": f"/{file_name_2}",
                    "media_type": "image/jpeg",
                    "size": 7958,
                },
                {
                    "name": file.name,
                    "kind": file.kind,
                    "parent_id": file.parent_id,
                    "volume_id": file.volume_id,
                    "path_from_vol": file.path_from_vol,
                    "media_type": file.media_type,
                    "size": file.size,
                },
            )
            self.assertEqual("Canon", file.metadata["Image Make"])
            self.assertEqual("Canon EOS 40D", file.metadata["Image Model"])
            self.assertIsNotNone(file.last_modified)

        # Test update
        with open(file_path, "w+") as f_h:
            f_h.write("\n")
        with transaction.atomic():
            perform_index(self.context.volume)
        files = File.objects.all()
        self.assertEqual(2, files.count())
        for file in files:
            if file == self.context.root_file:
                continue
            self.assertEqual(
                {
                    "name": file_name_2,
                    "kind": "file",
                    "parent_id": self.context.root_file.id,
                    "volume_id": self.context.volume.id,
                    "path_from_vol": f"/{file_name_2}",
                    "media_type": "image/jpeg",
                    "size": 1,
                    "metadata": {},
                },
                {
                    "name": file.name,
                    "kind": file.kind,
                    "parent_id": file.parent_id,
                    "volume_id": file.volume_id,
                    "path_from_vol": file.path_from_vol,
                    "media_type": file.media_type,
                    "size": file.size,
                    "metadata": file.metadata,
                },
            )
            self.assertIsNotNone(file.last_modified)

    def test_get_file_parents(self):
        """Test get_file_parents"""
        folder_name = "example"
        folder_path = os.path.join(self.context.root_path, folder_name)
        os.makedirs(folder_path)

        file_name = "log.txt"
        file_path = os.path.join(self.context.root_path, folder_name, file_name)
        with open(file_path, "w+") as f_h:
            f_h.write("")

        with transaction.atomic():
            perform_index(self.context.volume)

        folder_obj = File.objects.filter(name=folder_name).first()
        file_obj = File.objects.filter(name=file_name).first()
        self.assertEqual([], get_file_parents(self.context.root_file))
        self.assertEqual([self.context.root_file], get_file_parents(folder_obj))
        self.assertEqual(
            [self.context.root_file, folder_obj], get_file_parents(file_obj)
        )

    def test_perform_index_3(self):
        """Test perform_index (Invalid volume)"""
        self.context.volume.kind = VolumeKindEnum.REMOTE_RPI_DRIVE
        with self.assertRaises(InvalidVolumeKindException):
            perform_index(self.context.volume)

    def test_delete_file_1(self):
        """Test delete_file (Folder)"""
        folder_name = "example"
        folder_path = os.path.join(self.context.root_path, folder_name)
        os.makedirs(folder_path)

        file_name = "log.txt"
        file_path = os.path.join(self.context.root_path, folder_name, file_name)
        with open(file_path, "w+") as f_h:
            f_h.write("")

        with transaction.atomic():
            perform_index(self.context.volume)

        folder_obj = File.objects.filter(name=folder_name).first()
        delete_file(folder_obj)

        self.assertEqual(1, File.objects.count())
        self.assertEqual(self.context.root_file, File.objects.first())

    def test_delete_file_2(self):
        """Test delete_file (File)"""
        file_name = "log.txt"
        file_path = os.path.join(self.context.root_path, file_name)
        with open(file_path, "w+") as f_h:
            f_h.write("")

        with transaction.atomic():
            perform_index(self.context.volume)

        file_obj = File.objects.filter(name=file_name).first()
        delete_file(file_obj)

        self.assertEqual(1, File.objects.count())
        self.assertEqual(self.context.root_file, File.objects.first())

    def test_rename_file_1(self):
        """Test rename_file (No name)"""
        file_name = "log.txt"
        file_path = os.path.join(self.context.root_path, file_name)
        with open(file_path, "w+") as f_h:
            f_h.write("")
        file_obj = create_entry(
            self.context.volume,
            self.context.root_file,
            file_path,
        )

        with self.assertRaises(InvalidFileNameException) as ctx:
            rename_file(file_obj, "  ")
        self.assertEqual("File name can't be empty.", str(ctx.exception))
        file_obj.refresh_from_db()
        self.assertEqual(file_name, file_obj.name)
        self.assertTrue(os.path.exists(file_path))

    def test_rename_file_2(self):
        """Test rename_file (Used name)"""
        file_name_1 = "log.txt"
        file_path_1 = os.path.join(self.context.root_path, file_name_1)
        with open(file_path_1, "w+") as f_h:
            f_h.write("")
        file_obj_1 = create_entry(
            self.context.volume,
            self.context.root_file,
            file_path_1,
        )

        file_name_2 = "log2.txt"
        file_path_2 = os.path.join(self.context.root_path, file_name_2)
        with open(file_path_2, "w+") as f_h:
            f_h.write("")
        create_entry(
            self.context.volume,
            self.context.root_file,
            file_path_2,
        )

        with self.assertRaises(InvalidFileNameException) as ctx:
            rename_file(file_obj_1, file_name_2)
        self.assertEqual("File name is already in use.", str(ctx.exception))
        file_obj_1.refresh_from_db()
        self.assertEqual(file_name_1, file_obj_1.name)
        self.assertTrue(os.path.exists(file_path_1))

    def test_rename_file_3(self):
        """Test rename_file (Invalid char in name)"""
        file_name = "log.txt"
        file_path = os.path.join(self.context.root_path, file_name)
        with open(file_path, "w+") as f_h:
            f_h.write("")
        file_obj = create_entry(
            self.context.volume,
            self.context.root_file,
            file_path,
        )

        with self.assertRaises(InvalidFileNameException) as ctx:
            rename_file(file_obj, "a" + os.path.sep + "a")
        self.assertEqual("Invalid character in file name.", str(ctx.exception))
        file_obj.refresh_from_db()
        self.assertEqual(file_name, file_obj.name)
        self.assertTrue(os.path.exists(file_path))

    def test_rename_file_4(self):
        """Test rename_file"""
        file_name = "log.txt"
        file_path = os.path.join(self.context.root_path, file_name)
        with open(file_path, "w+") as f_h:
            f_h.write("")
        file_obj = create_entry(
            self.context.volume,
            self.context.root_file,
            file_path,
        )

        file_name_2 = "  zzz.txt"
        rename_file(file_obj, file_name_2)
        self.assertEqual("zzz.txt", file_obj.name)
        self.assertEqual("/zzz.txt", file_obj.path_from_vol)

    def test_compress_files_1(self):
        """Test compress_files (Invalid name)"""
        with self.assertRaises(InvalidFileNameException):
            compress_files([], self.context.root_file, "a" + os.path.sep + "a.zip")
        with self.assertRaises(InvalidFileNameException):
            compress_files([], self.context.root_file, "  ")

    def test_compress_files_2(self):
        """Test compress_files (No file)"""
        with self.assertRaises(NoFileException):
            compress_files([], self.context.root_file, "a.zip")

    def test_compress_files_3(self):
        """Test compress_files"""
        file_name = "log.txt"
        file_path = os.path.join(self.context.root_path, file_name)
        with open(file_path, "w+") as f_h:
            f_h.write("")
        file_obj = create_entry(
            self.context.volume,
            self.context.root_file,
            file_path,
        )

        job = compress_files([str(file_obj.id)], self.context.root_file, "a.zip")
        self.assertIsNotNone(job)

    def test_move_files_1(self):
        """Test move_files (Destination is file)"""
        file_name_1 = "log.txt"
        file_path_1 = os.path.join(self.context.root_path, file_name_1)
        with open(file_path_1, "w+") as f_h:
            f_h.write("")
        file_obj_1 = create_entry(
            self.context.volume,
            self.context.root_file,
            file_path_1,
        )

        file_name_2 = "log2.txt"
        file_path_2 = os.path.join(self.context.root_path, file_name_2)
        with open(file_path_2, "w+") as f_h:
            f_h.write("")
        file_obj_2 = create_entry(
            self.context.volume,
            self.context.root_file,
            file_path_2,
        )

        with self.assertRaises(InvalidOperationRequestException) as ctx:
            move_files([str(file_obj_1.id)], file_obj_2, True)
        self.assertEqual("Destination must be a folder.", str(ctx.exception))

    def test_move_files_2(self):
        """Test move_files (Same folder)"""
        folder_1 = os.path.join(self.context.root_path, "folder1")
        os.makedirs(folder_1)
        with transaction.atomic():
            perform_index(self.context.volume)
        folder_obj_1 = File.objects.get(name="folder1")

        with self.assertRaises(InvalidOperationRequestException) as ctx:
            move_files([str(folder_obj_1.id)], folder_obj_1, True)
        self.assertEqual("Invalid parent path.", str(ctx.exception))

    def test_move_files_4(self):
        """Test move_files (Move to subdirectory)"""
        folder_1_name = "folder1"
        folder_1 = os.path.join(self.context.root_path, folder_1_name)
        os.makedirs(folder_1)

        folder_2_name = "folder2"
        folder_2 = os.path.join(self.context.root_path, folder_1_name, folder_2_name)
        os.makedirs(folder_2)

        with transaction.atomic():
            perform_index(self.context.volume)

        folder_obj_1 = File.objects.get(name="folder1")
        folder_obj_2 = File.objects.get(name="folder2")

        with self.assertRaises(InvalidOperationRequestException) as ctx:
            move_files([str(folder_obj_1.id)], folder_obj_2, True)
        self.assertEqual("Invalid parent path.", str(ctx.exception))

    def test_move_files_5(self):  # pylint: disable=too-many-locals
        """Test move_files (Rename)"""
        folder_1_name = "folder1"
        folder_1 = os.path.join(self.context.root_path, folder_1_name)
        os.makedirs(folder_1)
        folder_1_obj = create_entry(
            self.context.volume,
            self.context.root_file,
            folder_1,
        )

        file_1_name = "log.txt"
        file_1 = os.path.join(self.context.root_path, folder_1_name, file_1_name)
        with open(file_1, "w+") as f_h:
            f_h.write("1")
        file_1_obj = create_entry(
            self.context.volume,
            folder_1_obj,
            file_1,
        )

        file_12_name = "logz.txt"
        file_12 = os.path.join(self.context.root_path, folder_1_name, file_12_name)
        with open(file_12, "w+") as f_h:
            f_h.write("12")
        file_12_obj = create_entry(
            self.context.volume,
            folder_1_obj,
            file_12,
        )

        folder_2_name = "folder2"
        folder_2 = os.path.join(self.context.root_path, folder_2_name)
        os.makedirs(folder_2)
        folder_2_obj = create_entry(
            self.context.volume,
            self.context.root_file,
            folder_2,
        )

        folder_21 = os.path.join(self.context.root_path, folder_2_name, folder_1_name)
        os.makedirs(folder_21)
        folder_21_obj = create_entry(
            self.context.volume,
            folder_2_obj,
            folder_21,
        )

        file_21 = os.path.join(
            self.context.root_path, folder_2_name, folder_1_name, file_1_name
        )
        with open(file_21, "w+") as f_h:
            f_h.write("21")
        file_21_obj = create_entry(
            self.context.volume,
            folder_21_obj,
            file_21,
        )

        move_files([str(folder_1_obj.id)], folder_2_obj, True)
        self.assertFalse(File.objects.filter(id=folder_1_obj.id).exists())

        # Check file is renamed
        self.assertTrue(File.objects.filter(id=file_1_obj.id).exists())
        file_1_obj.refresh_from_db()
        self.assertEqual("log (1).txt", file_1_obj.name)
        self.assertEqual(
            f"/{folder_2_name}/{folder_1_name}/log (1).txt", file_1_obj.path_from_vol
        )
        with open(get_full_path(file_1_obj), "r") as f_h:
            self.assertEqual("1", f_h.read())

        # Check file went through without conflict resolution
        self.assertTrue(File.objects.filter(id=file_12_obj.id).exists())
        file_12_obj.refresh_from_db()
        self.assertEqual(file_12_name, file_12_obj.name)
        self.assertEqual(
            f"/{folder_2_name}/{folder_1_name}/{file_12_name}",
            file_12_obj.path_from_vol,
        )
        with open(get_full_path(file_12_obj), "r") as f_h:
            self.assertEqual("12", f_h.read())

        # Check original file still in tact
        file_21_obj.refresh_from_db()
        self.assertEqual(file_1_name, file_21_obj.name)
        self.assertEqual(
            f"/{folder_2_name}/{folder_1_name}/{file_1_name}", file_21_obj.path_from_vol
        )
        with open(get_full_path(file_21_obj), "r") as f_h:
            self.assertEqual("21", f_h.read())

    def test_move_files_6(self):
        """Test move_files (Replace)"""
        folder_1_name = "folder1"
        folder_1 = os.path.join(self.context.root_path, folder_1_name)
        os.makedirs(folder_1)
        folder_1_obj = create_entry(
            self.context.volume,
            self.context.root_file,
            folder_1,
        )

        file_1_name = "log.txt"
        file_1 = os.path.join(self.context.root_path, folder_1_name, file_1_name)
        with open(file_1, "w+") as f_h:
            f_h.write("1")
        file_1_obj = create_entry(
            self.context.volume,
            folder_1_obj,
            file_1,
        )

        folder_2_name = "folder2"
        folder_2 = os.path.join(self.context.root_path, folder_2_name)
        os.makedirs(folder_2)
        folder_2_obj = create_entry(
            self.context.volume,
            self.context.root_file,
            folder_2,
        )

        folder_21 = os.path.join(self.context.root_path, folder_2_name, folder_1_name)
        os.makedirs(folder_21)
        folder_21_obj = create_entry(
            self.context.volume,
            folder_2_obj,
            folder_21,
        )

        file_21 = os.path.join(
            self.context.root_path, folder_2_name, folder_1_name, file_1_name
        )
        with open(file_21, "w+") as f_h:
            f_h.write("21")
        file_21_obj = create_entry(
            self.context.volume,
            folder_21_obj,
            file_21,
        )

        move_files([str(folder_1_obj.id)], folder_2_obj, False)
        self.assertFalse(File.objects.filter(id=folder_1_obj.id).exists())
        self.assertFalse(File.objects.filter(id=file_21_obj.id).exists())

        # Check destination file is replaced by source file
        self.assertTrue(File.objects.filter(id=file_1_obj.id).exists())
        file_1_obj.refresh_from_db()
        self.assertEqual("log.txt", file_1_obj.name)
        self.assertEqual(
            f"/{folder_2_name}/{folder_1_name}/log.txt", file_1_obj.path_from_vol
        )
        with open(get_full_path(file_1_obj), "r") as f_h:
            self.assertEqual("1", f_h.read())

    def test_create_folder_1(self):
        """Test create_folder (Empty name)"""
        with self.assertRaises(InvalidFileNameException) as ctx:
            create_folder(self.context.root_file, "  ")
        self.assertEqual("Folder name can't be empty.", str(ctx.exception))

    def test_create_folder_2(self):
        """Test create_folder (Invalid name)"""
        with self.assertRaises(InvalidFileNameException) as ctx:
            create_folder(self.context.root_file, "a" + os.path.sep + "a")
        self.assertEqual("Invalid character in folder name.", str(ctx.exception))

    def test_create_folder_3(self):
        """Test create_folder (Allows Duplicate name)"""
        folder_name = "example"
        folder_path = os.path.join(self.context.root_path, folder_name)
        os.makedirs(folder_path)
        folder_obj = create_entry(
            self.context.volume,
            self.context.root_file,
            folder_path,
        )

        folder_obj_2 = create_folder(self.context.root_file, folder_name, True)
        self.assertEqual(folder_obj, folder_obj_2)

    def test_create_folder_4(self):
        """Test create_folder (Disallows duplicate name)"""
        folder_name = "example"
        folder_path = os.path.join(self.context.root_path, folder_name)
        os.makedirs(folder_path)
        create_entry(
            self.context.volume,
            self.context.root_file,
            folder_path,
        )

        with self.assertRaises(InvalidFileNameException) as ctx:
            create_folder(self.context.root_file, folder_name)
        self.assertEqual("Folder name is already in use.", str(ctx.exception))
        self.assertEqual(2, File.objects.count())

    def test_create_folder_5(self):
        """Test create_folder"""
        folder = create_folder(self.context.root_file, "example")
        self.assertEqual("example", folder.name)
        self.assertEqual("folder", folder.kind)
        self.assertEqual(self.context.root_file, folder.parent)
        self.assertEqual(self.context.volume, folder.volume)
        self.assertIsNotNone(folder.last_modified)
        self.assertEqual("/example", folder.path_from_vol)

    def test_process_compress_job(self):
        """Test process_compress_job"""
        folder_name = "folder"
        folder_path = os.path.join(self.context.root_path, folder_name)
        os.makedirs(folder_path)
        folder_obj = create_entry(
            self.context.volume,
            self.context.root_file,
            folder_path,
        )

        file_name = "log.txt"
        file_path = os.path.join(self.context.root_path, file_name)
        with open(file_path, "w+") as f_h:
            f_h.write("")
        file_obj = create_entry(
            self.context.volume,
            self.context.root_file,
            file_path,
        )

        job = compress_files(
            [str(file_obj.id), str(folder_obj.id)], self.context.root_file, "a.zip"
        )
        output = process_compress_job(job)

        self.assertEqual(JobStatus.COMPLETED, job.status)
        self.assertTrue(os.path.exists(get_full_path(output)))
        self.assertEqual("a.zip", output.name)
        self.assertEqual(FileKindEnum.FILE, output.kind)
        self.assertEqual(self.context.root_file, output.parent)
        self.assertEqual(self.context.volume, output.volume)
        self.assertEqual("/a.zip", output.path_from_vol)
        self.assertEqual("application/zip", output.media_type)

        with ZipFile(get_full_path(output), "r") as zf:
            zf_list = {x.filename for x in zf.filelist}
        self.assertEqual({file_name, folder_name + os.path.sep}, zf_list)
