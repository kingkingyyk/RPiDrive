from django.test import TestCase
from ..utils.indexer import LocalStorageProviderIndexer, InvalidStorageProviderTypeException
from ..models import StorageProvider, StorageProviderType, FileObjectType, LocalFileObject, FileExt
from django.apps import apps
import os
import shutil


class TestLocalStorageProviderIndexer(TestCase):
    _TEST_PATH = 'test-indexer-temp'

    def setUp(self):
        os.makedirs(TestLocalStorageProviderIndexer._TEST_PATH, exist_ok=True)

        # Create FS objects!
        folder1 = os.path.join(
            TestLocalStorageProviderIndexer._TEST_PATH, 'folder1')
        folder2 = os.path.join(
            TestLocalStorageProviderIndexer._TEST_PATH, 'folder2')
        folder3 = os.path.join(folder2, 'folder3')
        folders = [folder1, folder2, folder3]
        for f in folders:
            os.makedirs(f, exist_ok=True)
        file1 = os.path.join(folder1, 'file1.txt')
        file2 = os.path.join(folder2, 'file2.mp3')
        file3 = os.path.join(folder3, 'file3.jpg')
        file4 = os.path.join(
            TestLocalStorageProviderIndexer._TEST_PATH, 'file4.py')
        files = [file1, file2, file3, file4]
        for f in files:
            with open(f, 'w+') as fh:
                fh.write(f)

        # Create DB objects
        sp = StorageProvider(name='test', type=StorageProviderType.LOCAL_PATH,
                             path=TestLocalStorageProviderIndexer._TEST_PATH)
        sp.save()

        root = LocalFileObject.objects.create(
            name='ROOT', obj_type=FileObjectType.FOLDER, rel_path='', storage_provider=sp)

    def tearDown(self):
        shutil.rmtree(TestLocalStorageProviderIndexer._TEST_PATH)
        StorageProvider.objects.all().delete()
        LocalFileObject.objects.all().delete()

    def test_construct_fs_tree(self):
        sp = StorageProvider.objects.first()
        path = sp.path

        root = LocalStorageProviderIndexer._construct_fs_tree(sp)
        root.children.sort(key=lambda x : x.name)
        self.assertEqual(root.path, path, 'Root children size')
        self.assertEqual(len(root.children), 3, 'Root children size')

        file4 = root.children[0]
        file4_name = 'file4.py'
        self.assertEqual(file4.name, file4_name, 'File4 name')
        self.assertEqual(file4.path, os.path.join(
            path, file4_name), 'File4 path')
        self.assertEqual(len(file4.children), 0, 'File4 children size')

        folder1 = root.children[1]
        folder1_name = 'folder1'
        self.assertEqual(folder1.name, folder1_name, 'Folder1 name')
        self.assertEqual(folder1.path, os.path.join(
            path, folder1_name), 'Folder1 path')
        self.assertEqual(len(folder1.children), 1, 'Folder1 children size')

        file1 = folder1.children[0]
        file1_name = 'file1.txt'
        self.assertEqual(file1.name, file1_name, 'File1 name')
        self.assertEqual(file1.path, os.path.join(
            folder1.path, file1_name), 'File1 path')
        self.assertEqual(len(file1.children), 0, 'File1 children size')

        folder2 = root.children[2]
        folder2_name = 'folder2'
        self.assertEqual(folder2.name, 'folder2', 'Folder2 name')
        self.assertEqual(folder2.path, os.path.join(
            path, folder2_name), 'Folder2 path')
        self.assertEqual(len(folder2.children), 2, 'Folder2 children size')

        file2 = folder2.children[0]
        file2_name = 'file2.mp3'
        self.assertEqual(file2.name, file2_name, 'File2 name')
        self.assertEqual(file2.path, os.path.join(
            folder2.path, file2_name), 'File2 path')
        self.assertEqual(len(file2.children), 0, 'File2 children size')

        folder3 = folder2.children[1]
        folder3_name = 'folder3'
        self.assertEqual(folder3.name, 'folder3', 'Folder3 name')
        self.assertEqual(folder3.path, os.path.join(
            folder2.path, folder3_name), 'Folder3 path')
        self.assertEqual(len(folder3.children), 1, 'Folder3 children size')

        file3 = folder3.children[0]
        file3_name = 'file3.jpg'
        self.assertEqual(file3.name, file3_name, 'File3 name')
        self.assertEqual(file3.path, os.path.join(
            folder3.path, file3_name), 'File3 path')
        self.assertEqual(len(file3.children), 0, 'File3 children size')

    def test_construct_db_tree(self):
        sp = StorageProvider.objects.first()
        root = LocalFileObject.objects.get(storage_provider=sp)
        qs = LocalStorageProviderIndexer._construct_db_tree(root)
        self.assertIsNotNone(qs)

    def test_clean_sync_db(self):
        sp = StorageProvider.objects.first()
        root = LocalFileObject.objects.get(storage_provider=sp)
        LocalStorageProviderIndexer.sync(root)

        lfos = LocalFileObject.objects.order_by('rel_path').all()
        expected_results = [
            ('ROOT', ''),
            ('file4.py', os.path.join('file4.py')),
            ('folder1', os.path.join('folder1')),
            ('file1.txt', os.path.join('folder1', 'file1.txt')),
            ('folder2', os.path.join('folder2')),
            ('file2.mp3', os.path.join('folder2', 'file2.mp3')),
            ('folder3', os.path.join('folder2', 'folder3')),
            ('file3.jpg', os.path.join('folder2', 'folder3', 'file3.jpg')),
        ]
        for idx, result in enumerate(expected_results):
            lfo = lfos[idx]
            self.assertEqual(lfo.name, result[0], 'Wrong name')
            self.assertEqual(lfo.rel_path, result[1], 'Wrong relative path')
            if idx > 0:
                pardir = os.path.dirname(lfo.rel_path)
                expected_parent = LocalFileObject.objects.get(rel_path=pardir)
                self.assertEqual(
                    lfo.parent.pk, expected_parent.pk, 'Wrong parent')
            else:
                self.assertIsNone(lfo.parent, 'Wrong parent')
            self.assertEqual(lfo.storage_provider.pk, sp.pk,
                             'Wring storage_provider')
            self.assertIsNotNone(lfo.last_modified, 'Wrong last_modified')
            self.assertEqual(lfo.full_path, os.path.join(
                lfo.storage_provider.path, lfo.rel_path), 'Wrong full_path')
            self.assertEqual(lfo.size, os.path.getsize(
                lfo.full_path), 'Wrong size')
            if os.path.isdir(lfo.full_path):
                self.assertIsNone(lfo.extension, 'Wrong folder.extension')
                self.assertEqual(
                    lfo.obj_type, FileObjectType.FOLDER, 'Wrong folder.obj_type')
                self.assertIsNone(lfo.type, 'Wrong folder.type')
            elif os.path.isfile(lfo.full_path):
                print(lfo.name)
                print(lfo.extension)
                self.assertIsNotNone(lfo.extension, 'Wrong file.extension #1')
                self.assertTrue(lfo.name.endswith(
                    '.'+lfo.extension), 'Wrong file.extension #2')
                self.assertEqual(
                    lfo.obj_type, FileObjectType.FILE, 'Wrong file.obj_type')
                self.assertEqual(lfo.type, FileExt.resolve_extension(
                    lfo.extension), 'Wrong file.type')

    def test_sync_db_deletion(self):
        sp = StorageProvider.objects.first()
        root = LocalFileObject.objects.get(storage_provider=sp)
        LocalStorageProviderIndexer.sync(root)

        root_id = LocalFileObject.objects.get(rel_path='').pk
        folder1_id = LocalFileObject.objects.get(
            rel_path=os.path.join('folder1')).pk
        file4_id = LocalFileObject.objects.get(
            rel_path=os.path.join('file4.py')).pk
        file1_id = LocalFileObject.objects.get(
            rel_path=os.path.join('folder1', 'file1.txt')).pk

        shutil.rmtree(os.path.join(
            TestLocalStorageProviderIndexer._TEST_PATH, 'folder2'))
        LocalStorageProviderIndexer.sync(root)

        expected_results = [root_id, file4_id, folder1_id, file1_id]
        lfos = LocalFileObject.objects.order_by('rel_path').all()
        for idx, result in enumerate(expected_results):
            lfo = lfos[idx]
            self.assertEqual(lfo.pk, result, 'LocalFileObject.ID')

    def test_non_local_storage_provider(self):
        sp = StorageProvider.objects.first()
        root = LocalFileObject.objects.get(storage_provider=sp)
        root.storage_provider.type = 'dummy'
        with self.assertRaises(InvalidStorageProviderTypeException):
            LocalStorageProviderIndexer.sync(root)