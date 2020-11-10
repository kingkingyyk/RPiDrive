from django.test import TestCase
from ..utils.indexer import LocalStorageProviderIndexer
from ..models import StorageProvider, StorageProviderType, FileObjectType, LocalFileObject, FileExt
import os
import shutil


class TestLocalFileObject(TestCase):
    _TEST_PATH = 'test-model-temp'

    def setUp(self):
        os.makedirs(TestLocalFileObject._TEST_PATH, exist_ok=True)
        os.mkdir(os.path.join(TestLocalFileObject._TEST_PATH, 'folder'))
        with open(os.path.join(TestLocalFileObject._TEST_PATH, 'file.java'), 'w+') as f:
            f.write('something')

        # Create DB objects
        sp = StorageProvider(
            name='test', type=StorageProviderType.LOCAL_PATH, path=TestLocalFileObject._TEST_PATH)
        sp.save()
        root = LocalFileObject.objects.create(
            name='ROOT', obj_type=FileObjectType.FOLDER, rel_path='', storage_provider=sp)
        LocalStorageProviderIndexer.sync(root)

    def tearDown(self):
        shutil.rmtree(TestLocalFileObject._TEST_PATH)
        StorageProvider.objects.all().delete()
        LocalFileObject.objects.all().delete()

    def test_query_ordering(self):
        sp = StorageProvider.objects.first()
        root = LocalFileObject.objects.get(
            storage_provider__pk=sp.pk, parent=None)
        children = root.children.all()
        expected_files = ['folder', 'file.java']

        for idx, file in enumerate(expected_files):
            self.assertEqual(children[idx].name, file, 'Wrong order')
