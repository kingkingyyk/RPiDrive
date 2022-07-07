import os
import shutil
from django.test import TestCase
from drive.utils.indexer import LocalStorageProviderIndexer
from drive.models import (
    StorageProvider,
    StorageProviderType,
    FileObjectType,
    LocalFileObject,
)


class TestLocalFileObject(TestCase):
    """Test local file object operations"""
    _TEST_PATH = 'test-model-temp'

    def setUp(self):
        os.makedirs(TestLocalFileObject._TEST_PATH, exist_ok=True)
        os.mkdir(os.path.join(TestLocalFileObject._TEST_PATH, 'folder'))
        with open(os.path.join(TestLocalFileObject._TEST_PATH, 'file.java'), 'w+') as f_h:
            f_h.write('something')

        # Create DB objects
        s_p = StorageProvider(
            name='test', type=StorageProviderType.LOCAL_PATH, path=TestLocalFileObject._TEST_PATH)
        s_p.save()
        root = LocalFileObject.objects.create(
            name='ROOT', obj_type=FileObjectType.FOLDER, rel_path='', storage_provider=s_p)
        LocalStorageProviderIndexer.sync(root)

    def tearDown(self):
        shutil.rmtree(TestLocalFileObject._TEST_PATH)
        StorageProvider.objects.all().delete()
        LocalFileObject.objects.all().delete()

    def test_query_ordering(self):
        """Test file object query ordering"""
        s_p = StorageProvider.objects.first()
        root = LocalFileObject.objects.get(
            storage_provider__pk=s_p.pk, parent=None)
        children = root.children.all()
        expected_files = ['folder', 'file.java']

        for idx, file in enumerate(expected_files):
            self.assertEqual(children[idx].name, file, 'Wrong order')
