import os
import shutil
import uuid

from django.contrib.auth.models import User
from django.db import transaction
from django.test import TestCase

from rpidrive.controllers.file import FileNotFoundException
from rpidrive.controllers.local_file import perform_index
from rpidrive.controllers.playlists import (
    InvalidNameException,
    PlaylistNotFoundException,
    PlaylistFileNotFoundException,
    add_playlist_file,
    create_playlist,
    delete_playlist,
    get_playlist,
    get_playlists,
    remove_playlist_file,
    reorder_playlist_file,
    update_playlist,
)
from rpidrive.models import (
    Playlist,
    PlaylistFile,
    File,
)
from rpidrive.tests.helpers.setup import SetupContext


class TestPlaylistController(TestCase):  # pylint: disable=too-many-public-methods
    """Test playlist controller"""

    def setUp(self):
        self.context = SetupContext()
        self.other_user = User.objects.create_user("XD")

    def tearDown(self):
        self.context.cleanup()
        User.objects.all().delete()
        Playlist.objects.all().delete()

    def test_get_playlists(self):
        """Test get_playlists"""
        pl_1 = create_playlist(self.context.admin, "p1")
        pl_2 = create_playlist(self.context.admin, "p2")
        pl_3 = create_playlist(self.other_user, "p1")

        pl_list_1 = get_playlists(self.context.admin).all()
        self.assertEqual({pl_1, pl_2}, set(pl_list_1))

        pl_list_2 = get_playlists(self.other_user).all()
        self.assertEqual({pl_3}, set(pl_list_2))

    def test_get_playlist_1(self):
        """Test get_playlist"""
        pl_1 = create_playlist(self.context.admin, "p1")
        pl_2 = get_playlist(self.context.admin, pl_1.id)
        self.assertEqual(pl_2, pl_1)

        with self.assertRaises(PlaylistNotFoundException):
            get_playlist(self.other_user, pl_1.id)

    def test_get_playlist_2(self):
        """Test get_playlist (Write)"""
        pl_1 = create_playlist(self.context.admin, "p1")
        pl_2 = get_playlist(self.context.admin, pl_1.id, write=True)
        self.assertEqual(pl_2, pl_1)

    def test_get_playlist_3(self):
        """Test get_playlist (Invalid id)"""
        with self.assertRaises(PlaylistNotFoundException):
            get_playlist(self.context.admin, str(uuid.uuid4()), write=True)

    def test_create_playlist_1(self):
        """Test create_playlist"""
        pl = create_playlist(self.context.admin, "  zz")
        self.assertEqual("zz", pl.name)
        self.assertEqual(self.context.admin, pl.owner)

    def test_create_playlist_2(self):
        """Test create_playlist (Invalid name)"""
        with self.assertRaises(InvalidNameException):
            create_playlist(self.context.admin, "  ")
        self.assertFalse(Playlist.objects.exists())

    def test_update_playlist_1(self):
        """Test update_playlist"""
        pl = create_playlist(self.context.admin, "  zz")
        pl = update_playlist(self.context.admin, pl.id, "gg ")
        self.assertEqual("gg", pl.name)

    def test_update_playlist_2(self):
        """Test update_playlist (Invalid name)"""
        pl = create_playlist(self.context.admin, "  zz")
        with self.assertRaises(InvalidNameException):
            update_playlist(self.context.admin, pl.id, "")
        pl.refresh_from_db()
        self.assertEqual("zz", pl.name)

    def test_update_playlist_3(self):
        """Test update_playlist (Invalid id)"""
        with self.assertRaises(PlaylistNotFoundException):
            update_playlist(self.context.admin, str(uuid.uuid4()), "gg")

    def test_update_playlist_4(self):
        """Test update_playlist (Invalid user)"""
        pl = create_playlist(self.context.admin, "  zz")
        with self.assertRaises(PlaylistNotFoundException):
            update_playlist(self.other_user, pl.id, "gg")

    def test_add_playlist_file_1(self):
        """Test add_playlist_file"""
        file_name = "sample.m4a"
        file_name_2 = "sample2.m4a"
        src_file = os.path.join(
            os.path.dirname(os.path.realpath(__file__)), "sample.m4a"
        )
        file_path = os.path.join(self.context.root_path, file_name)
        shutil.copy2(src_file, file_path)
        file_path_2 = os.path.join(self.context.root_path, file_name_2)
        shutil.copy2(src_file, file_path_2)

        with transaction.atomic():
            perform_index(self.context.volume)

        pl = create_playlist(self.context.admin, "XD")

        file = File.objects.filter(name=file_name).first()
        pl = add_playlist_file(self.context.admin, str(pl.id), str(file.id))
        pl_file = PlaylistFile.objects.filter(file=file).first()
        self.assertIsNotNone(pl_file)
        self.assertEqual(pl_file.playlist_id, pl.id)
        self.assertEqual(pl_file.file_id, file.id)
        self.assertEqual(0, pl_file.sequence)

        file_2 = File.objects.filter(name=file_name_2).first()
        pl = add_playlist_file(self.context.admin, str(pl.id), str(file_2.id))
        pl_file = PlaylistFile.objects.filter(file=file_2).first()
        self.assertIsNotNone(pl_file)
        self.assertEqual(pl_file.playlist_id, pl.id)
        self.assertEqual(pl_file.file_id, file_2.id)
        self.assertEqual(1, pl_file.sequence)

    def test_add_playlist_file_2(self):
        """Test add_playlist_file (Invalid playlist id)"""
        file_name = "sample.m4a"
        src_file = os.path.join(
            os.path.dirname(os.path.realpath(__file__)), "sample.m4a"
        )
        file_path = os.path.join(self.context.root_path, file_name)
        shutil.copy2(src_file, file_path)

        with transaction.atomic():
            perform_index(self.context.volume)
        file = File.objects.filter(name=file_name).first()

        with self.assertRaises(PlaylistNotFoundException):
            add_playlist_file(self.context.admin, str(uuid.uuid4()), str(file.id))

    def test_add_playlist_file_3(self):
        """Test add_playlist_file (Invalid file id)"""
        pl = create_playlist(self.context.admin, "XD")
        with self.assertRaises(FileNotFoundException):
            add_playlist_file(self.context.admin, str(pl.id), str(uuid.uuid4()))

    def test_add_playlist_file_4(self):
        """Test add_playlist_file (Invalid user)"""
        file_name = "sample.m4a"
        src_file = os.path.join(
            os.path.dirname(os.path.realpath(__file__)), "sample.m4a"
        )
        file_path = os.path.join(self.context.root_path, file_name)
        shutil.copy2(src_file, file_path)

        with transaction.atomic():
            perform_index(self.context.volume)
        file = File.objects.filter(name=file_name).first()

        pl = create_playlist(self.context.admin, "XD")
        with self.assertRaises(PlaylistNotFoundException):
            add_playlist_file(self.other_user, str(pl.id), str(file.id))

    def test_remove_playlist_file_1(self):
        """Test remove_playlist_file"""
        file_name = "sample.m4a"
        file_name_2 = "sample2.m4a"
        src_file = os.path.join(
            os.path.dirname(os.path.realpath(__file__)), "sample.m4a"
        )
        file_path = os.path.join(self.context.root_path, file_name)
        shutil.copy2(src_file, file_path)
        file_path_2 = os.path.join(self.context.root_path, file_name_2)
        shutil.copy2(src_file, file_path_2)

        with transaction.atomic():
            perform_index(self.context.volume)
        file = File.objects.filter(name=file_name).first()
        file_2 = File.objects.filter(name=file_name_2).first()

        pl = create_playlist(self.context.admin, "XD")
        add_playlist_file(self.context.admin, str(pl.id), str(file.id))
        add_playlist_file(self.context.admin, str(pl.id), str(file_2.id))

        pl_file = PlaylistFile.objects.filter(
            playlist=pl,
            sequence=0,
        ).first()
        pl_file_2 = PlaylistFile.objects.filter(
            playlist=pl,
            sequence=1,
        ).first()

        remove_playlist_file(self.context.admin, str(pl.id), str(pl_file.id))
        self.assertEqual(1, PlaylistFile.objects.count())
        self.assertEqual(pl_file_2, PlaylistFile.objects.first())

    def test_remove_playlist_file_2(self):
        """Test remove_playlist_file (Invalid playlist id)"""
        file_name = "sample.m4a"
        src_file = os.path.join(
            os.path.dirname(os.path.realpath(__file__)), "sample.m4a"
        )
        file_path = os.path.join(self.context.root_path, file_name)
        shutil.copy2(src_file, file_path)

        with transaction.atomic():
            perform_index(self.context.volume)
        file = File.objects.filter(name=file_name).first()

        pl = create_playlist(self.context.admin, "XD")
        add_playlist_file(self.context.admin, str(pl.id), str(file.id))
        pl_file = PlaylistFile.objects.filter(
            playlist=pl,
            sequence=0,
        ).first()

        with self.assertRaises(PlaylistNotFoundException):
            remove_playlist_file(self.context.admin, str(uuid.uuid4()), str(pl_file.id))

    def test_remove_playlist_file_3(self):
        """Test remove_playlist_file (Invalid user)"""
        file_name = "sample.m4a"
        src_file = os.path.join(
            os.path.dirname(os.path.realpath(__file__)), "sample.m4a"
        )
        file_path = os.path.join(self.context.root_path, file_name)
        shutil.copy2(src_file, file_path)

        with transaction.atomic():
            perform_index(self.context.volume)
        file = File.objects.filter(name=file_name).first()

        pl = create_playlist(self.context.admin, "XD")
        add_playlist_file(self.context.admin, str(pl.id), str(file.id))
        pl_file = PlaylistFile.objects.filter(
            playlist=pl,
            sequence=0,
        ).first()

        with self.assertRaises(PlaylistNotFoundException):
            remove_playlist_file(self.other_user, str(pl.id), pl_file.id)
        self.assertEqual(1, PlaylistFile.objects.count())

    def test_remove_playlist_file_4(self):
        """Test remove_playlist_file (Invalid playlist file)"""
        pl = create_playlist(self.context.admin, "XD")

        with self.assertRaises(PlaylistFileNotFoundException):
            remove_playlist_file(self.context.admin, str(pl.id), 999)

    def test_reorder_playlist_file_1(self):
        """Test reorder_playlist_file"""
        file_name = "sample.m4a"
        file_name_2 = "sample2.m4a"
        src_file = os.path.join(
            os.path.dirname(os.path.realpath(__file__)), "sample.m4a"
        )
        file_path = os.path.join(self.context.root_path, file_name)
        shutil.copy2(src_file, file_path)
        file_path_2 = os.path.join(self.context.root_path, file_name_2)
        shutil.copy2(src_file, file_path_2)

        with transaction.atomic():
            perform_index(self.context.volume)
        file = File.objects.filter(name=file_name).first()
        file_2 = File.objects.filter(name=file_name_2).first()

        pl = create_playlist(self.context.admin, "XD")
        add_playlist_file(self.context.admin, str(pl.id), str(file.id))
        add_playlist_file(self.context.admin, str(pl.id), str(file_2.id))

        pl_file = PlaylistFile.objects.filter(
            playlist=pl,
            sequence=0,
        ).first()
        pl_file_2 = PlaylistFile.objects.filter(
            playlist=pl,
            sequence=1,
        ).first()

        reorder_playlist_file(
            self.context.admin, str(pl.id), [pl_file_2.id, pl_file.id]
        )
        pl_file.refresh_from_db()
        pl_file_2.refresh_from_db()
        self.assertEqual(1, pl_file.sequence)
        self.assertEqual(0, pl_file_2.sequence)

    def test_reorder_playlist_file_2(self):
        """Test reorder_playlist_file (Invalid playlist id)"""
        with self.assertRaises(PlaylistNotFoundException):
            reorder_playlist_file(self.other_user, str(uuid.uuid4()), [])

    def test_reorder_playlist_file_3(self):
        """Test reorder_playlist_file (Invalid user)"""
        file_name = "sample.m4a"
        file_name_2 = "sample2.m4a"
        src_file = os.path.join(
            os.path.dirname(os.path.realpath(__file__)), "sample.m4a"
        )
        file_path = os.path.join(self.context.root_path, file_name)
        shutil.copy2(src_file, file_path)
        file_path_2 = os.path.join(self.context.root_path, file_name_2)
        shutil.copy2(src_file, file_path_2)

        with transaction.atomic():
            perform_index(self.context.volume)
        file = File.objects.filter(name=file_name).first()
        file_2 = File.objects.filter(name=file_name_2).first()

        pl = create_playlist(self.context.admin, "XD")
        add_playlist_file(self.context.admin, str(pl.id), str(file.id))
        add_playlist_file(self.context.admin, str(pl.id), str(file_2.id))

        pl_file = PlaylistFile.objects.filter(
            playlist=pl,
            sequence=0,
        ).first()
        pl_file_2 = PlaylistFile.objects.filter(
            playlist=pl,
            sequence=1,
        ).first()

        with self.assertRaises(PlaylistNotFoundException):
            reorder_playlist_file(
                self.other_user, str(pl.id), [pl_file_2.id, pl_file.id]
            )

        pl_file.refresh_from_db()
        pl_file_2.refresh_from_db()
        self.assertEqual(0, pl_file.sequence)
        self.assertEqual(1, pl_file_2.sequence)

    def test_delete_playlist_1(self):
        """Test delete_playlist"""
        pl = create_playlist(self.context.admin, "p1")
        delete_playlist(self.context.admin, pl.id)
        self.assertEqual(0, Playlist.objects.count())

    def test_delete_playlist_2(self):
        """Test delete_playlist (Invalid user)"""
        pl = create_playlist(self.context.admin, "p1")
        with self.assertRaises(PlaylistNotFoundException):
            delete_playlist(self.other_user, pl.id)
        self.assertEqual(1, Playlist.objects.count())

    def test_delete_playlist_3(self):
        """Test delete_playlist (Invalid playlist id)"""
        create_playlist(self.context.admin, "p1")
        with self.assertRaises(PlaylistNotFoundException):
            delete_playlist(self.other_user, str(uuid.uuid4()))
        self.assertEqual(1, Playlist.objects.count())
