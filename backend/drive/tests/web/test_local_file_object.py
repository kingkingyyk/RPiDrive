# pylint: disable=too-many-lines
import http
import json
import os
import shutil
import tempfile

from datetime import timedelta
from uuid import uuid4
from zipfile import ZipFile

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db.models import Q
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from drive.cache import ModelCache
from drive.core.storage_provider import create_storage_provider_helper
from drive.management.commands.jobserver import Command
from drive.models import (
    FileObjectAlias,
    FileObjectTypeEnum,
    Job,
    LocalFileObject,
    StorageProvider,
    StorageProviderTypeEnum,
    StorageProviderUser,
)
from drive.request_models import MoveFileStrategy
from drive.tests.web.shared import MIMETYPE_JSON
from drive.utils.indexer import LocalStorageProviderIndexer

class TestLocalFileObject(TestCase): # pylint: disable=too-many-public-methods
    """Test local file object views"""

    def _get_manage_url(self, i_d: str):
        return reverse('file.manage', args=[i_d])

    def _get_quick_access_url(self, i_d: str):
        return reverse('file.quick-access', args=[i_d])

    def _get_download_url(self, i_d: str):
        return reverse('file.download', args=[i_d])

    def setUp(self):
        self.search_url = reverse('file.search')
        self.move_url = reverse('file.move')
        self.zip_url = reverse('file.zip')
        self.req_qa_file_url = reverse('file.req-quick-access')
        self.admin_user = User.objects.create_superuser(
            username='adminz'
        )
        self.user = User.objects.create_user(
            username='noob'
        )
        self.root_test_dir = os.path.join(tempfile.gettempdir(), 'rpidrive')
        os.makedirs(self.root_test_dir, exist_ok=True)

    def tearDown(self):
        ModelCache.flush()

        Job.objects.all().delete()
        LocalFileObject.objects.all().delete()
        StorageProvider.objects.all().delete()
        User.objects.all().delete()

        shutil.rmtree(self.root_test_dir)

    def test_search_url(self):
        """Test search_file url"""
        self.assertEqual(
            '/drive/web-api/files/search',
            self.search_url
        )

    def test_search_methods(self):
        """Test search_file methods"""
        # Not logged in
        response = self.client.get(self.search_url)
        self.assertEqual(http.HTTPStatus.UNAUTHORIZED, response.status_code)

        response = self.client.post(self.search_url)
        self.assertEqual(http.HTTPStatus.UNAUTHORIZED, response.status_code)

        response = self.client.put(self.search_url)
        self.assertEqual(http.HTTPStatus.UNAUTHORIZED, response.status_code)

        response = self.client.delete(self.search_url)
        self.assertEqual(http.HTTPStatus.UNAUTHORIZED, response.status_code)

        # Logged in
        self.client.force_login(self.user)
        response = self.client.post(self.search_url)
        self.assertEqual(http.HTTPStatus.METHOD_NOT_ALLOWED, response.status_code)

        response = self.client.put(self.search_url)
        self.assertEqual(http.HTTPStatus.METHOD_NOT_ALLOWED, response.status_code)

        response = self.client.delete(self.search_url)
        self.assertEqual(http.HTTPStatus.METHOD_NOT_ALLOWED, response.status_code)

    def test_search(self):
        """Test search_file"""
        # Prepare SP1
        sp1_path = os.path.join(self.root_test_dir, 'sp1')
        os.makedirs(sp1_path, exist_ok=True)
        _, root_1 = create_storage_provider_helper(
            'sp1',
            StorageProviderTypeEnum.LOCAL_PATH.value,
            sp1_path,
        )
        with open(os.path.join(sp1_path, '01 file.txt'), 'w+') as f_h:
            f_h.write('')
        os.makedirs(os.path.join(sp1_path, '02 file'))
        with open(os.path.join(sp1_path, '02 file', 'file3.txt'), 'w+') as f_h:
            f_h.write('')
        LocalStorageProviderIndexer.sync(root_1)

        # Prepare 2
        sp2_path = os.path.join(self.root_test_dir, 'sp2')
        os.makedirs(sp2_path, exist_ok=True)
        sp_2, root_2 = create_storage_provider_helper(
            'sp2',
            StorageProviderTypeEnum.LOCAL_PATH.value,
            sp2_path,
        )
        with open(os.path.join(sp2_path, '01 file.txt'), 'w+') as f_h:
            f_h.write('')
        os.makedirs(os.path.join(sp2_path, '02 file'))
        with open(os.path.join(sp2_path, '02 file', 'file3.txt'), 'w+') as f_h:
            f_h.write('')
        LocalStorageProviderIndexer.sync(root_2)

        # Login as admin user
        self.client.force_login(self.admin_user)
        # Search without keyword
        response = self.client.get(self.search_url)
        self.assertEqual(http.HTTPStatus.BAD_REQUEST, response.status_code)
        self.assertEqual(dict(error='Keyword not found.'), response.json())
        # Search file
        response = self.client.get(
            self.search_url,
            dict(keyword='file')
        )
        self.assertEqual(http.HTTPStatus.OK, response.status_code)
        expected_qs = (
            LocalFileObject.objects
            .filter(
                Q(name__search='file') | Q(name__icontains='file')
            )
            .order_by('-last_modified', 'name')
            .all()
        )
        values = response.json()['values']
        for value in values:
            self.assertIsNotNone(value['lastModified'])
            del value['lastModified']
        self.assertEqual(6, len(values))
        self.assertEqual([
            dict(
                id=str(file_obj.pk),
                name=file_obj.name,
                objType=file_obj.obj_type,
                relPath=file_obj.rel_path,
                extension=file_obj.extension,
                type=file_obj.type,
                size=file_obj.size,
                parent=dict(
                    id=str(file_obj.parent.pk),
                    name=file_obj.parent.name,
                    objType=file_obj.obj_type,
                ),
                storageProvider=dict(
                    id=file_obj.storage_provider.pk,
                    name=file_obj.storage_provider.name,
                    path=file_obj.storage_provider.path,
                )
            ) for file_obj in expected_qs
        ], values)
        # Search file2
        response = self.client.get(
            self.search_url,
            dict(keyword='file3')
        )
        self.assertEqual(http.HTTPStatus.OK, response.status_code)
        self.assertEqual(2, len(response.json()['values']))
        # Search ABC
        response = self.client.get(
            self.search_url,
            dict(keyword='ABC')
        )
        self.assertEqual(http.HTTPStatus.OK, response.status_code)
        self.assertEqual(0, len(response.json()['values']))

        # Login as normal user
        self.client.force_login(self.user)
        # Search file
        response = self.client.get(
            self.search_url,
            dict(keyword='file')
        )
        self.assertEqual(http.HTTPStatus.OK, response.status_code)
        self.assertEqual(0, len(response.json()['values']))
        # Grant sp_2 permission & search file again (limited to sp_2)
        StorageProviderUser.objects.create(
            storage_provider=sp_2,
            user=self.user,
            permission=StorageProviderUser.PERMISSION.READ,
        )
        response = self.client.get(
            self.search_url,
            dict(keyword='file')
        )
        self.assertEqual(http.HTTPStatus.OK, response.status_code)
        values = response.json()['values']
        for value in values:
            self.assertIsNotNone(value['lastModified'])
            del value['lastModified']
        self.assertEqual(3, len(values))
        expected_qs = (
            LocalFileObject.objects
            .filter(
                Q(name__search='file') | Q(name__icontains='file'),
                storage_provider=sp_2,
            )
            .order_by('-last_modified', 'name')
            .all()
        )
        self.assertEqual([
            dict(
                id=str(file_obj.pk),
                name=file_obj.name,
                objType=file_obj.obj_type,
                relPath=file_obj.rel_path,
                extension=file_obj.extension,
                type=file_obj.type,
                size=file_obj.size,
                parent=dict(
                    id=str(file_obj.parent.pk),
                    name=file_obj.parent.name,
                    objType=file_obj.obj_type,
                ),
                storageProvider=dict(
                    id=file_obj.storage_provider.pk,
                    name=file_obj.storage_provider.name,
                    path=file_obj.storage_provider.path,
                )
            ) for file_obj in expected_qs
        ], values)

    def test_move_url(self):
        """Test move_files url"""
        self.assertEqual(
            '/drive/web-api/files/move',
            self.move_url
        )

    def test_move_methods(self):
        """Test move_files methods"""
        # Not logged in
        response = self.client.get(self.move_url)
        self.assertEqual(http.HTTPStatus.UNAUTHORIZED, response.status_code)

        response = self.client.post(self.move_url)
        self.assertEqual(http.HTTPStatus.UNAUTHORIZED, response.status_code)

        response = self.client.put(self.move_url)
        self.assertEqual(http.HTTPStatus.UNAUTHORIZED, response.status_code)

        response = self.client.delete(self.move_url)
        self.assertEqual(http.HTTPStatus.UNAUTHORIZED, response.status_code)

        # Logged in
        self.client.force_login(self.user)
        response = self.client.get(self.move_url)
        self.assertEqual(http.HTTPStatus.METHOD_NOT_ALLOWED, response.status_code)

        response = self.client.put(self.move_url)
        self.assertEqual(http.HTTPStatus.METHOD_NOT_ALLOWED, response.status_code)

        response = self.client.delete(self.move_url)
        self.assertEqual(http.HTTPStatus.METHOD_NOT_ALLOWED, response.status_code)

    def test_move_basic(self):
        """Test move_files"""
        # Prepare SP
        sp_path = os.path.join(self.root_test_dir, 'sp')
        os.makedirs(sp_path, exist_ok=True)
        _, root = create_storage_provider_helper(
            'sp1',
            StorageProviderTypeEnum.LOCAL_PATH.value,
            sp_path,
        )
        with open(os.path.join(sp_path, '01 file.txt'), 'w+') as f_h:
            f_h.write('abc')
        os.makedirs(os.path.join(sp_path, 'fold'))
        with open(os.path.join(sp_path, 'fold', '02.zip'), 'w+') as f_h:
            f_h.write('axd')
        LocalStorageProviderIndexer.sync(root)

        file_1 = LocalFileObject.objects.get(name='01 file.txt')
        folder = LocalFileObject.objects.get(name='fold')
        file_2 = LocalFileObject.objects.get(name='02.zip')

        # Login as admin user
        self.client.force_login(self.admin_user)
        # Invalid destination
        response = self.client.post(
            self.move_url,
            dict(
                files=[
                    str(file_1.pk),
                ],
                destination=str(uuid4()),
                strategy=MoveFileStrategy.OVERWRITE,
            ),
            content_type=MIMETYPE_JSON,
        )
        self.assertEqual(http.HTTPStatus.BAD_REQUEST, response.status_code)
        self.assertEqual(
            dict(error='Destination folder doesn\'t exist!'),
            response.json()
        )
        # Destination is not a folder
        response = self.client.post(
            self.move_url,
            dict(
                files=[
                    str(file_1.pk),
                ],
                destination=str(file_2.pk),
                strategy=MoveFileStrategy.OVERWRITE,
            ),
            content_type=MIMETYPE_JSON,
        )
        self.assertEqual(http.HTTPStatus.BAD_REQUEST, response.status_code)
        self.assertEqual(
            dict(error='Destination must be a folder!'),
            response.json()
        )
        # Must be from same level
        response = self.client.post(
            self.move_url,
            dict(
                files=[
                    str(file_1.pk),
                    str(file_2.pk),
                ],
                destination=str(folder.pk),
                strategy=MoveFileStrategy.OVERWRITE,
            ),
            content_type=MIMETYPE_JSON,
        )
        self.assertEqual(http.HTTPStatus.BAD_REQUEST, response.status_code)
        self.assertEqual(
            dict(error='Only can move items in the same level!'),
            response.json()
        )
        # Move to same folder
        response = self.client.post(
            self.move_url,
            dict(
                files=[
                    str(file_2.pk),
                ],
                destination=str(folder.pk),
                strategy=MoveFileStrategy.RENAME,
            ),
            content_type=MIMETYPE_JSON,
        )
        self.assertEqual(http.HTTPStatus.OK, response.status_code)
        self.assertEqual({}, response.json())
        file_2.refresh_from_db()
        self.assertEqual('02.zip', file_2.name)
        # Move into folder
        response = self.client.post(
            self.move_url,
            dict(
                files=[
                    str(file_1.pk),
                ],
                destination=str(folder.pk),
                strategy=MoveFileStrategy.RENAME,
            ),
            content_type=MIMETYPE_JSON,
        )
        self.assertEqual(http.HTTPStatus.OK, response.status_code)
        self.assertEqual({}, response.json())
        file_1.refresh_from_db()
        self.assertEqual(folder, file_1.parent)
        self.assertTrue(os.path.isfile(file_1.full_path))
        self.assertFalse(os.path.exists(
            os.path.join(root.full_path, file_1.name)
        ))
        # Move parent into children
        response = self.client.post(
            self.move_url,
            dict(
                files=[
                    str(root.pk),
                ],
                destination=str(folder.pk),
                strategy=MoveFileStrategy.RENAME,
            ),
            content_type=MIMETYPE_JSON,
        )
        self.assertEqual(http.HTTPStatus.INTERNAL_SERVER_ERROR, response.status_code)
        self.assertEqual(dict(error=f'Failed to move:\n{root.full_path}'), response.json())
        self.assertTrue(os.path.isdir(root.full_path))
        self.assertTrue(os.path.isdir(folder.full_path))

    def test_move_permission(self):
        """Test move_files (permission)"""
        # Prepare SP
        sp_path = os.path.join(self.root_test_dir, 'sp')
        os.makedirs(sp_path, exist_ok=True)
        s_p, root = create_storage_provider_helper(
            'sp1',
            StorageProviderTypeEnum.LOCAL_PATH.value,
            sp_path,
        )
        with open(os.path.join(sp_path, '01 file.txt'), 'w+') as f_h:
            f_h.write('abc')
        os.makedirs(os.path.join(sp_path, 'fold'))
        with open(os.path.join(sp_path, 'fold', '02.zip'), 'w+') as f_h:
            f_h.write('axd')
        LocalStorageProviderIndexer.sync(root)

        file_1 = LocalFileObject.objects.get(name='01 file.txt')
        folder = LocalFileObject.objects.get(name='fold')

        self.client.force_login(self.user)
        response = self.client.post(
            self.move_url,
            dict(
                files=[
                    str(file_1.pk),
                ],
                destination=str(folder.pk),
                strategy=MoveFileStrategy.RENAME,
            ),
            content_type=MIMETYPE_JSON,
        )
        self.assertEqual(http.HTTPStatus.FORBIDDEN, response.status_code)
        self.assertEqual(
            dict(error='No permission to perform the operation!'),
            response.json()
        )

        # Gives READ permission
        StorageProviderUser.objects.create(
            storage_provider=s_p,
            user=self.user,
            permission=StorageProviderUser.PERMISSION.READ
        )
        response = self.client.post(
            self.move_url,
            dict(
                files=[
                    str(file_1.pk),
                ],
                destination=str(folder.pk),
                strategy=MoveFileStrategy.RENAME,
            ),
            content_type=MIMETYPE_JSON,
        )
        self.assertEqual(http.HTTPStatus.FORBIDDEN, response.status_code)
        self.assertEqual(
            dict(error='No permission to perform the operation!'),
            response.json()
        )

        # Gives READ-WRITE permission
        StorageProviderUser.objects.filter(
            storage_provider=s_p,
            user=self.user,
        ).update(
            permission=StorageProviderUser.PERMISSION.READ_WRITE
        )
        response = self.client.post(
            self.move_url,
            dict(
                files=[
                    str(file_1.pk),
                ],
                destination=str(folder.pk),
                strategy=MoveFileStrategy.RENAME,
            ),
            content_type=MIMETYPE_JSON,
        )
        self.assertEqual(http.HTTPStatus.OK, response.status_code)
        self.assertEqual({}, response.json())

    def test_move_strategy_rename_1(self):
        """Test move_files (rename strategy) - 1"""
        # Prepare SP
        sp_path = os.path.join(self.root_test_dir, 'sp')
        os.makedirs(sp_path, exist_ok=True)
        _, root = create_storage_provider_helper(
            'sp1',
            StorageProviderTypeEnum.LOCAL_PATH.value,
            sp_path,
        )
        with open(os.path.join(sp_path, '01.zip'), 'w+') as f_h:
            f_h.write('abc')
        os.makedirs(os.path.join(sp_path, 'fold'))
        with open(os.path.join(sp_path, 'fold', '01.zip'), 'w+') as f_h:
            f_h.write('axd')
        LocalStorageProviderIndexer.sync(root)

        file_1 = LocalFileObject.objects.get(name='01.zip', parent=root)
        folder = LocalFileObject.objects.get(name='fold')
        file_2 = LocalFileObject.objects.get(name='01.zip', parent=folder)

        # Move into folder
        self.client.force_login(self.admin_user)
        response = self.client.post(
            self.move_url,
            dict(
                files=[
                    str(file_1.pk),
                ],
                destination=str(folder.pk),
                strategy=MoveFileStrategy.RENAME,
            ),
            content_type=MIMETYPE_JSON,
        )
        self.assertEqual(http.HTTPStatus.OK, response.status_code)
        self.assertEqual({}, response.json())

        # Check db level
        file_1.refresh_from_db()
        self.assertEqual('01 (1).zip', file_1.name)
        self.assertEqual(
            os.path.join(folder.full_path, file_1.name),
            file_1.full_path,
        )
        self.assertEqual(folder, file_1.parent)
        file_2.refresh_from_db()
        self.assertEqual('01.zip', file_2.name)
        self.assertEqual(
            os.path.join(folder.full_path, file_2.name),
            file_2.full_path,
        )
        self.assertEqual(folder, file_2.parent)

        # Check from file level
        self.assertFalse(os.path.exists(os.path.join(root.full_path, '01.zip')))
        self.assertTrue(os.path.exists(file_1.full_path))
        self.assertTrue(os.path.exists(file_2.full_path))

    def test_move_strategy_rename_2(self):
        """Test move_files (rename strategy) - 2"""
        # Prepare SP
        sp_path = os.path.join(self.root_test_dir, 'sp')
        os.makedirs(sp_path, exist_ok=True)
        _, root = create_storage_provider_helper(
            'sp1',
            StorageProviderTypeEnum.LOCAL_PATH.value,
            sp_path,
        )
        with open(os.path.join(sp_path, '01.zip'), 'w+') as f_h:
            f_h.write('abc')
        os.makedirs(os.path.join(sp_path, 'fold'))
        os.makedirs(os.path.join(sp_path, 'fold', '01.zip'))
        LocalStorageProviderIndexer.sync(root)

        file = LocalFileObject.objects.get(name='01.zip', parent=root)
        folder_1 = LocalFileObject.objects.get(name='fold')
        folder_2 = LocalFileObject.objects.get(name='01.zip', parent=folder_1)

        # Move into folder (src same name with a folder in destination)
        self.client.force_login(self.admin_user)
        response = self.client.post(
            self.move_url,
            dict(
                files=[
                    str(file.pk),
                ],
                destination=str(folder_1.pk),
                strategy=MoveFileStrategy.RENAME,
            ),
            content_type=MIMETYPE_JSON,
        )
        self.assertEqual(http.HTTPStatus.OK, response.status_code)
        self.assertEqual({}, response.json())

        # Check db level
        file.refresh_from_db()
        self.assertEqual('01 (1).zip', file.name)
        self.assertEqual(
            os.path.join(folder_1.full_path, file.name),
            file.full_path,
        )
        self.assertEqual(folder_1, file.parent)
        folder_2.refresh_from_db()
        self.assertEqual('01.zip', folder_2.name)
        self.assertEqual(
            os.path.join(folder_1.full_path, folder_2.name),
            folder_2.full_path,
        )
        self.assertEqual(folder_1, folder_2.parent)

        # Check from file level
        self.assertFalse(os.path.exists(os.path.join(root.full_path, '01.zip')))
        self.assertTrue(os.path.exists(file.full_path))
        self.assertTrue(os.path.exists(folder_2.full_path))

    def test_move_strategy_rename_3(self):
        """Test move_files (rename strategy) - Folder merging"""
        # Prepare SP
        sp_path = os.path.join(self.root_test_dir, 'sp')
        os.makedirs(sp_path, exist_ok=True)
        _, root = create_storage_provider_helper(
            'sp1',
            StorageProviderTypeEnum.LOCAL_PATH.value,
            sp_path,
        )
        os.makedirs(os.path.join(sp_path, 'f1'))
        with open(os.path.join(sp_path, 'f1', '01.zip'), 'w+') as f_h:
            f_h.write('abc')
        os.makedirs(os.path.join(sp_path, 'f2'))
        os.makedirs(os.path.join(sp_path, 'f2', 'f1'))
        with open(os.path.join(sp_path, 'f2', 'f1', '01.zip'), 'w+') as f_h:
            f_h.write('abc')
        LocalStorageProviderIndexer.sync(root)

        folder_1 = LocalFileObject.objects.get(name='f1', parent=root)
        file_1 = LocalFileObject.objects.get(name='01.zip', parent=folder_1)
        folder_2 = LocalFileObject.objects.get(name='f2')
        folder_21 = LocalFileObject.objects.get(name='f1', parent=folder_2)
        file_2 = LocalFileObject.objects.get(name='01.zip', parent=folder_21)

        # Move folder into folder
        self.client.force_login(self.admin_user)
        response = self.client.post(
            self.move_url,
            dict(
                files=[
                    str(folder_21.pk),
                ],
                destination=str(root.pk),
                strategy=MoveFileStrategy.RENAME,
            ),
            content_type=MIMETYPE_JSON,
        )
        self.assertEqual(http.HTTPStatus.OK, response.status_code)
        self.assertEqual({}, response.json())

        # Check db level
        file_1.refresh_from_db()
        self.assertEqual('01.zip', file_1.name)
        self.assertEqual(
            os.path.join(folder_1.full_path, file_1.name),
            file_1.full_path,
        )
        self.assertEqual(folder_1, file_1.parent)
        file_2.refresh_from_db()
        self.assertEqual('01 (1).zip', file_2.name)
        self.assertEqual(
            os.path.join(folder_1.full_path, file_2.name),
            file_2.full_path,
        )
        self.assertEqual(folder_1, file_2.parent)
        self.assertEqual(folder_1, LocalFileObject.objects.get(name='f1', parent=root))
        self.assertFalse(LocalFileObject.objects.filter(pk=folder_21.pk).exists())
        # Check from file level
        self.assertFalse(os.path.exists(folder_21.full_path))
        self.assertTrue(os.path.exists(folder_2.full_path))
        self.assertTrue(os.path.exists(file_1.full_path))
        self.assertTrue(os.path.exists(file_2.full_path))

    def test_move_strategy_rename_autoname(self):
        """Test move_files (rename strategy) - autoname"""
        # Prepare SP
        sp_path = os.path.join(self.root_test_dir, 'sp')
        os.makedirs(sp_path, exist_ok=True)
        _, root = create_storage_provider_helper(
            'sp1',
            StorageProviderTypeEnum.LOCAL_PATH.value,
            sp_path,
        )
        with open(os.path.join(sp_path, '01'), 'w+') as f_h:
            f_h.write('abc')
        os.makedirs(os.path.join(sp_path, 'fold'))
        with open(os.path.join(sp_path, 'fold', '01'), 'w+') as f_h:
            f_h.write('axd')
        LocalStorageProviderIndexer.sync(root)

        # Test file extension rename
        file_1 = LocalFileObject.objects.get(name='01', parent=root)
        folder = LocalFileObject.objects.get(name='fold')
        file_2 = LocalFileObject.objects.get(name='01', parent=folder)

        # Move into folder
        self.client.force_login(self.admin_user)
        response = self.client.post(
            self.move_url,
            dict(
                files=[
                    str(file_1.pk),
                ],
                destination=str(folder.pk),
                strategy=MoveFileStrategy.RENAME,
            ),
            content_type=MIMETYPE_JSON,
        )
        self.assertEqual(http.HTTPStatus.OK, response.status_code)
        self.assertEqual({}, response.json())

        # Check db level
        file_1.refresh_from_db()
        self.assertEqual('01 (1)', file_1.name)
        self.assertEqual(
            os.path.join(folder.full_path, file_1.name),
            file_1.full_path,
        )
        self.assertEqual(folder, file_1.parent)
        file_2.refresh_from_db()
        self.assertEqual('01', file_2.name)
        self.assertEqual(
            os.path.join(folder.full_path, file_2.name),
            file_2.full_path,
        )
        self.assertEqual(folder, file_2.parent)

        # Check from file level
        self.assertFalse(os.path.exists(os.path.join(root.full_path, '01.zip')))
        self.assertTrue(os.path.exists(file_1.full_path))
        self.assertTrue(os.path.exists(file_2.full_path))

    def test_move_strategy_overwrite_1(self):
        """Test move_files (overwrite strategy)"""
        # Prepare SP
        sp_path = os.path.join(self.root_test_dir, 'sp')
        os.makedirs(sp_path, exist_ok=True)
        _, root = create_storage_provider_helper(
            'sp1',
            StorageProviderTypeEnum.LOCAL_PATH.value,
            sp_path,
        )
        with open(os.path.join(sp_path, '01.zip'), 'w+') as f_h:
            f_h.write('abc')
        os.makedirs(os.path.join(sp_path, 'fold'))
        with open(os.path.join(sp_path, 'fold', '01.zip'), 'w+') as f_h:
            f_h.write('axd')
        LocalStorageProviderIndexer.sync(root)

        file_1 = LocalFileObject.objects.get(name='01.zip', parent=root)
        folder = LocalFileObject.objects.get(name='fold')
        file_2 = LocalFileObject.objects.get(name='01.zip', parent=folder)

        # Move into folder
        self.client.force_login(self.admin_user)
        response = self.client.post(
            self.move_url,
            dict(
                files=[
                    str(file_1.pk),
                ],
                destination=str(folder.pk),
                strategy=MoveFileStrategy.OVERWRITE,
            ),
            content_type=MIMETYPE_JSON,
        )
        self.assertEqual(http.HTTPStatus.OK, response.status_code)
        self.assertEqual({}, response.json())

        # Check db level
        file_1.refresh_from_db()
        self.assertEqual('01.zip', file_1.name)
        self.assertEqual(
            os.path.join(folder.full_path, file_1.name),
            file_1.full_path,
        )
        self.assertEqual(folder, file_1.parent)
        self.assertEqual(file_1, LocalFileObject.objects.get(name='01.zip'))
        self.assertFalse(LocalFileObject.objects.filter(pk=file_2.pk).exists())

        # Check from file level
        self.assertFalse(os.path.exists(os.path.join(root.full_path, '01.zip')))
        self.assertTrue(os.path.exists(file_1.full_path))

    def test_move_strategy_overwrite_2(self):
        """Test move_files (overwrite strategy) - 2"""
        # Prepare SP
        sp_path = os.path.join(self.root_test_dir, 'sp')
        os.makedirs(sp_path, exist_ok=True)
        _, root = create_storage_provider_helper(
            'sp1',
            StorageProviderTypeEnum.LOCAL_PATH.value,
            sp_path,
        )
        with open(os.path.join(sp_path, '01.zip'), 'w+') as f_h:
            f_h.write('abc')
        os.makedirs(os.path.join(sp_path, 'fold'))
        os.makedirs(os.path.join(sp_path, 'fold', '01.zip'))
        LocalStorageProviderIndexer.sync(root)

        file = LocalFileObject.objects.get(name='01.zip', parent=root)
        folder_1 = LocalFileObject.objects.get(name='fold')
        folder_2 = LocalFileObject.objects.get(name='01.zip', parent=folder_1)

        # Move into folder (src same name with a folder in destination)
        self.client.force_login(self.admin_user)
        response = self.client.post(
            self.move_url,
            dict(
                files=[
                    str(file.pk),
                ],
                destination=str(folder_1.pk),
                strategy=MoveFileStrategy.OVERWRITE,
            ),
            content_type=MIMETYPE_JSON,
        )
        self.assertEqual(http.HTTPStatus.OK, response.status_code)
        self.assertEqual({}, response.json())

        # Check db level
        file.refresh_from_db()
        self.assertEqual('01 (1).zip', file.name)
        self.assertEqual(
            os.path.join(folder_1.full_path, file.name),
            file.full_path,
        )
        self.assertEqual(folder_1, file.parent)
        folder_2.refresh_from_db()
        self.assertEqual('01.zip', folder_2.name)
        self.assertEqual(
            os.path.join(folder_1.full_path, folder_2.name),
            folder_2.full_path,
        )
        self.assertEqual(folder_1, folder_2.parent)

        # Check from file level
        self.assertFalse(os.path.exists(os.path.join(root.full_path, '01.zip')))
        self.assertTrue(os.path.exists(file.full_path))
        self.assertTrue(os.path.exists(folder_2.full_path))

    def test_move_strategy_overwrite_3(self):
        """Test move_files (overwrite strategy) - Folder merging"""
        # Prepare SP
        sp_path = os.path.join(self.root_test_dir, 'sp')
        os.makedirs(sp_path, exist_ok=True)
        _, root = create_storage_provider_helper(
            'sp1',
            StorageProviderTypeEnum.LOCAL_PATH.value,
            sp_path,
        )
        os.makedirs(os.path.join(sp_path, 'f1'))
        with open(os.path.join(sp_path, 'f1', '01.zip'), 'w+') as f_h:
            f_h.write('abc')
        os.makedirs(os.path.join(sp_path, 'f2'))
        os.makedirs(os.path.join(sp_path, 'f2', 'f1'))
        with open(os.path.join(sp_path, 'f2', 'f1', '01.zip'), 'w+') as f_h:
            f_h.write('abc')
        LocalStorageProviderIndexer.sync(root)

        folder_1 = LocalFileObject.objects.get(name='f1', parent=root)
        file_1 = LocalFileObject.objects.get(name='01.zip', parent=folder_1)
        folder_2 = LocalFileObject.objects.get(name='f2')
        folder_21 = LocalFileObject.objects.get(name='f1', parent=folder_2)
        file_2 = LocalFileObject.objects.get(name='01.zip', parent=folder_21)

        # Move folder into folder
        self.client.force_login(self.admin_user)
        response = self.client.post(
            self.move_url,
            dict(
                files=[
                    str(folder_21.pk),
                ],
                destination=str(root.pk),
                strategy=MoveFileStrategy.OVERWRITE,
            ),
            content_type=MIMETYPE_JSON,
        )
        self.assertEqual(http.HTTPStatus.OK, response.status_code)
        self.assertEqual({}, response.json())

        # Check db level
        self.assertFalse(LocalFileObject.objects.filter(pk=folder_21.pk).exists())
        self.assertFalse(LocalFileObject.objects.filter(pk=file_1.pk).exists())
        self.assertEqual(file_2, LocalFileObject.objects.get(name='01.zip', parent=folder_1))
        file_2.refresh_from_db()
        self.assertEqual('01.zip', file_2.name)
        self.assertEqual(
            os.path.join(folder_1.full_path, file_2.name),
            file_2.full_path,
        )
        self.assertEqual(folder_1, file_2.parent)
        self.assertEqual(folder_1, LocalFileObject.objects.get(name='f1', parent=root))
        # Check from file level
        self.assertFalse(os.path.exists(folder_21.full_path))
        self.assertTrue(os.path.exists(folder_2.full_path))
        self.assertTrue(os.path.exists(file_2.full_path))

    def test_move_cross_sp(self):
        """Test move_files (Cross storage provider)"""
        # Prepare SP 1
        sp_path = os.path.join(self.root_test_dir, 'sp1')
        os.makedirs(sp_path, exist_ok=True)
        _, root_1 = create_storage_provider_helper(
            'sp1',
            StorageProviderTypeEnum.LOCAL_PATH.value,
            sp_path,
        )
        LocalStorageProviderIndexer.sync(root_1)

        # Prepare SP 2
        sp_path = os.path.join(self.root_test_dir, 'sp2')
        os.makedirs(sp_path, exist_ok=True)
        _, root_2 = create_storage_provider_helper(
            'sp2',
            StorageProviderTypeEnum.LOCAL_PATH.value,
            sp_path,
        )
        LocalStorageProviderIndexer.sync(root_1)

        # Files with different storage provider
        self.client.force_login(self.admin_user)
        response = self.client.post(
            self.move_url,
            dict(
                files=[
                    str(root_2.pk),
                    str(root_1.pk),
                ],
                destination=str(root_1.pk),
                strategy=MoveFileStrategy.OVERWRITE,
            ),
            content_type=MIMETYPE_JSON,
        )
        self.assertEqual(http.HTTPStatus.BAD_REQUEST, response.status_code)
        self.assertEqual(
            dict(error='Files must be under same storage provider!'),
            response.json()
        )

        # File to different storage provider
        response = self.client.post(
            self.move_url,
            dict(
                files=[
                    str(root_2.pk),
                ],
                destination=str(root_1.pk),
                strategy=MoveFileStrategy.OVERWRITE,
            ),
            content_type=MIMETYPE_JSON,
        )
        self.assertEqual(http.HTTPStatus.BAD_REQUEST, response.status_code)
        self.assertEqual(
            dict(error='Source & destination must have same storage provider!'),
            response.json()
        )

    def test_zip_url(self):
        """Test zip_files url"""
        self.assertEqual(
            '/drive/web-api/files/zip',
            self.zip_url
        )

    def test_zip_methods(self):
        """Test zip_files methods"""
        # Not logged in
        response = self.client.get(self.zip_url)
        self.assertEqual(http.HTTPStatus.UNAUTHORIZED, response.status_code)

        response = self.client.post(self.zip_url)
        self.assertEqual(http.HTTPStatus.UNAUTHORIZED, response.status_code)

        response = self.client.put(self.zip_url)
        self.assertEqual(http.HTTPStatus.UNAUTHORIZED, response.status_code)

        response = self.client.delete(self.zip_url)
        self.assertEqual(http.HTTPStatus.UNAUTHORIZED, response.status_code)

        # Logged in
        self.client.force_login(self.user)
        response = self.client.get(self.zip_url)
        self.assertEqual(http.HTTPStatus.METHOD_NOT_ALLOWED, response.status_code)

        response = self.client.put(self.zip_url)
        self.assertEqual(http.HTTPStatus.METHOD_NOT_ALLOWED, response.status_code)

        response = self.client.delete(self.zip_url)
        self.assertEqual(http.HTTPStatus.METHOD_NOT_ALLOWED, response.status_code)

    def test_zip(self): # pylint: disable=too-many-statements
        """Test zip_files"""
        # Prepare SP
        sp_path = os.path.join(self.root_test_dir, 'sp')
        os.makedirs(sp_path, exist_ok=True)
        s_p, root = create_storage_provider_helper(
            'sp1',
            StorageProviderTypeEnum.LOCAL_PATH.value,
            sp_path,
        )
        with open(os.path.join(sp_path, '01 file.txt'), 'w+') as f_h:
            f_h.write('abc')
        os.makedirs(os.path.join(sp_path, 'fold'))
        with open(os.path.join(sp_path, 'fold', '02.zip'), 'w+') as f_h:
            f_h.write('axd')
        LocalStorageProviderIndexer.sync(root)

        file_1 = LocalFileObject.objects.get(name='01 file.txt')
        folder = LocalFileObject.objects.get(name='fold')

        # Invalid destination folder
        self.client.force_login(self.admin_user)
        response = self.client.post(
            self.zip_url,
            dict(
                files=[
                    str(file_1.pk),
                    str(folder.pk),
                ],
                destination=str(uuid4()),
                filename='compressed.zip',
            ),
            content_type=MIMETYPE_JSON,
        )
        self.assertEqual(http.HTTPStatus.BAD_REQUEST, response.status_code)
        self.assertEqual(dict(error='Destination folder doesn\'t exist!'), response.json())
        # Invalid destination
        response = self.client.post(
            self.zip_url,
            dict(
                files=[
                    str(file_1.pk),
                    str(folder.pk),
                ],
                destination=str(file_1.pk),
                filename='compressed.zip',
            ),
            content_type=MIMETYPE_JSON,
        )
        self.assertEqual(http.HTTPStatus.BAD_REQUEST, response.status_code)
        self.assertEqual(dict(error='Destination must be a folder!'), response.json())
        # Empty filename
        response = self.client.post(
            self.zip_url,
            dict(
                files=[
                    str(file_1.pk),
                    str(folder.pk),
                ],
                destination=str(folder.pk),
                filename='',
            ),
            content_type=MIMETYPE_JSON,
        )
        self.assertEqual(http.HTTPStatus.BAD_REQUEST, response.status_code)
        self.assertEqual(dict(error='Invalid name!'), response.json())
        # Invalid filename
        response = self.client.post(
            self.zip_url,
            dict(
                files=[
                    str(file_1.pk),
                    str(folder.pk),
                ],
                destination=str(folder.pk),
                filename='?!@',
            ),
            content_type=MIMETYPE_JSON,
        )
        self.assertEqual(http.HTTPStatus.BAD_REQUEST, response.status_code)
        self.assertEqual(dict(error='Invalid name!'), response.json())
        # Duplicate filename
        response = self.client.post(
            self.zip_url,
            dict(
                files=[
                    str(file_1.pk),
                    str(folder.pk),
                ],
                destination=str(folder.pk),
                filename='02',
            ),
            content_type=MIMETYPE_JSON,
        )
        self.assertEqual(http.HTTPStatus.BAD_REQUEST, response.status_code)
        self.assertEqual(dict(error='Name is already used by another file.'), response.json())
        # Valid filename
        req_data = dict(
            files=[
                str(file_1.pk),
                str(folder.pk),
            ],
            destination=str(folder.pk),
            filename='03.zip',
        )
        response = self.client.post(
            self.zip_url,
            req_data,
            content_type=MIMETYPE_JSON,
        )
        self.assertEqual(http.HTTPStatus.OK, response.status_code)
        self.assertEqual({}, response.json())
        self.assertEqual(1, Job.objects.count())
        job = Job.objects.get()
        self.assertEqual(json.dumps(req_data), job.data)
        # Run job server once
        Command.process_jobs()
        self.assertEqual(0, Job.objects.count())
        zip_file = LocalFileObject.objects.filter(name='03.zip', parent=folder).first()
        self.assertIsNotNone(zip_file)
        with ZipFile(zip_file.full_path, 'r') as z_f:
            self.assertEqual(['01 file.txt', 'fold/', 'fold/02.zip'], z_f.namelist())

        # Login as normal user
        # Valid filename (No permission)
        self.client.force_login(self.user)
        req_data = dict(
            files=[
                str(file_1.pk),
                str(folder.pk),
            ],
            destination=str(folder.pk),
            filename='03.zip',
        )
        response = self.client.post(
            self.zip_url,
            req_data,
            content_type=MIMETYPE_JSON,
        )
        self.assertEqual(http.HTTPStatus.FORBIDDEN, response.status_code)
        self.assertEqual(dict(error='No permission to perform the operation!'), response.json())
        # Valid filename (With permission)
        StorageProviderUser.objects.create(
            storage_provider=s_p,
            user=self.user,
            permission=StorageProviderUser.PERMISSION.READ_WRITE,
        )
        req_data = dict(
            files=[
                str(file_1.pk),
                str(folder.pk),
            ],
            destination=str(folder.pk),
            filename='04.zip',
        )
        response = self.client.post(
            self.zip_url,
            req_data,
            content_type=MIMETYPE_JSON,
        )
        self.assertEqual(http.HTTPStatus.OK, response.status_code)
        self.assertEqual({}, response.json())
        self.assertEqual(1, Job.objects.count())
        job = Job.objects.get()
        self.assertEqual(json.dumps(req_data), job.data)

    def test_manage_url(self):
        """Test manage_file url"""
        p_k = str(uuid4())
        self.assertEqual(
            f'/drive/web-api/files/{p_k}',
            self._get_manage_url(p_k)
        )

    def test_manage_methods(self):
        """Test manage_file methods"""
        url = self._get_manage_url(str(uuid4()))

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
        self.client.force_login(self.user)
        response = self.client.put(url)
        self.assertEqual(http.HTTPStatus.METHOD_NOT_ALLOWED, response.status_code)

    def test_quick_access_url(self):
        """Test generate_quick_access_link url"""
        p_k = str(uuid4())
        self.assertEqual(
            f'/drive/web-api/files/{p_k}/quick-access',
            self._get_quick_access_url(p_k)
        )

    def test_quick_access_methods(self):
        """Test generate_quick_access_link methoods"""
        url = self._get_quick_access_url(str(uuid4()))

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
        self.client.force_login(self.user)
        response = self.client.get(url)
        self.assertEqual(http.HTTPStatus.METHOD_NOT_ALLOWED, response.status_code)

        response = self.client.put(url)
        self.assertEqual(http.HTTPStatus.METHOD_NOT_ALLOWED, response.status_code)

        response = self.client.delete(url)
        self.assertEqual(http.HTTPStatus.METHOD_NOT_ALLOWED, response.status_code)

    def test_generate_quick_access_link(self):
        """Test generate_quick_access_link"""
        # Prepare SP
        sp_path = os.path.join(self.root_test_dir, 'sp')
        os.makedirs(sp_path, exist_ok=True)
        s_p, root = create_storage_provider_helper(
            'sp1',
            StorageProviderTypeEnum.LOCAL_PATH.value,
            sp_path,
        )
        with open(os.path.join(sp_path, '01 file.txt'), 'w+') as f_h:
            f_h.write('')
        LocalStorageProviderIndexer.sync(root)
        file_obj = LocalFileObject.objects.filter(name='01 file.txt').first()
        url = self._get_quick_access_url(file_obj.pk)

        # Not logged in
        response = self.client.post(url)
        self.assertEqual(http.HTTPStatus.UNAUTHORIZED, response.status_code)

        # Logged in as user without permission
        self.client.force_login(self.user)
        response = self.client.post(url)
        self.assertEqual(http.HTTPStatus.FORBIDDEN, response.status_code)
        self.assertEqual(
            dict(error='No permission to create quick access link!'),
            response.json()
        )
        # Invalid file
        response = self.client.post(self._get_quick_access_url(str(uuid4())))
        self.assertEqual(http.HTTPStatus.NOT_FOUND, response.status_code)
        self.assertEqual(
            dict(error='File not found!'),
            response.json()
        )

        # Logged in as user with READ permission
        sp_user = StorageProviderUser(
            storage_provider=s_p,
            user=self.user,
            permission=StorageProviderUser.PERMISSION.READ,
        )
        sp_user.save()
        response = self.client.post(url)
        self.assertEqual(http.HTTPStatus.FORBIDDEN, response.status_code)
        self.assertEqual(
            dict(error='No permission to create quick access link!'),
            response.json()
        )

        # Logged in as user with READ WRITE permission
        sp_user.permission = StorageProviderUser.PERMISSION.READ_WRITE
        sp_user.save()
        response = self.client.post(url)
        self.assertEqual(http.HTTPStatus.OK, response.status_code)
        self.assertTrue('key' in response.json())
        self.assertEqual(1, FileObjectAlias.objects.count())
        f_alias = FileObjectAlias.objects.first()
        self.assertEqual(file_obj, f_alias.local_ref)
        self.assertEqual(self.user, f_alias.creator)
        self.assertTrue(f_alias.expire_time - timezone.now() <= timedelta(minutes=10) )

        # Logged in as admin
        self.client.force_login(self.user)
        response = self.client.post(url)
        self.assertEqual(http.HTTPStatus.OK, response.status_code)
        self.assertTrue('key' in response.json())
        self.assertEqual(2, FileObjectAlias.objects.count())
        # Folder
        response = self.client.post(self._get_quick_access_url(root.pk))
        self.assertEqual(http.HTTPStatus.BAD_REQUEST, response.status_code)
        self.assertEqual(dict(error='Target file is a folder!'), response.json())
        # Invalid file
        response = self.client.post(self._get_quick_access_url(str(uuid4())))
        self.assertEqual(http.HTTPStatus.NOT_FOUND, response.status_code)
        self.assertEqual(
            dict(error='File not found!'),
            response.json()
        )

        # Try download
        response = self.client.get(
            self.req_qa_file_url,
            dict(key=str(f_alias.pk))
        )
        self.assertEqual(http.HTTPStatus.OK, response.status_code)
        self.assertTrue(response.streaming)

    def test_req_qa_file_url(self):
        """Test request_quick_access_file url"""
        self.assertEqual(
            '/drive/quick-access',
            self.req_qa_file_url
        )

    def test_req_qa_file_methods(self):
        """Test request_quick_access_file methods"""
        response = self.client.post(self.req_qa_file_url)
        self.assertEqual(http.HTTPStatus.METHOD_NOT_ALLOWED, response.status_code)

        response = self.client.put(self.req_qa_file_url)
        self.assertEqual(http.HTTPStatus.METHOD_NOT_ALLOWED, response.status_code)

        response = self.client.delete(self.req_qa_file_url)
        self.assertEqual(http.HTTPStatus.METHOD_NOT_ALLOWED, response.status_code)

    def test_req_qa_file(self):
        """Test request_quick_access_file"""
        # Missing key query param
        response = self.client.get(self.req_qa_file_url)
        self.assertEqual(http.HTTPStatus.NOT_FOUND, response.status_code)
        # Not UUID
        response = self.client.get(
            self.req_qa_file_url,
            dict(key='something')
        )
        self.assertEqual(http.HTTPStatus.NOT_FOUND, response.status_code)
        # Invalid UUID
        response = self.client.get(
            self.req_qa_file_url,
            dict(key=str(uuid4()))
        )
        self.assertEqual(http.HTTPStatus.NOT_FOUND, response.status_code)

        # Prepare SP
        sp_path = os.path.join(self.root_test_dir, 'sp')
        os.makedirs(sp_path, exist_ok=True)
        _, root = create_storage_provider_helper(
            'sp1',
            StorageProviderTypeEnum.LOCAL_PATH.value,
            sp_path,
        )
        with open(os.path.join(sp_path, '01 file.txt'), 'w+') as f_h:
            f_h.write('')
        LocalStorageProviderIndexer.sync(root)
        file_obj = LocalFileObject.objects.filter(name='01 file.txt').first()

        # Request expired link
        f_alias = FileObjectAlias.objects.create(
            local_ref=file_obj,
            creator=self.admin_user,
            expire_time=timezone.now() - timedelta(minutes=1)
        )
        response = self.client.get(
            self.req_qa_file_url,
            dict(key=str(f_alias.pk))
        )
        self.assertEqual(http.HTTPStatus.NOT_FOUND, response.status_code)
        self.assertEqual(0, FileObjectAlias.objects.count())

        # Request a valid link
        f_alias = FileObjectAlias.objects.create(
            local_ref=file_obj,
            creator=self.admin_user,
            expire_time=timezone.now() + timedelta(minutes=1)
        )
        response = self.client.get(
            self.req_qa_file_url,
            dict(key=str(f_alias.pk))
        )
        self.assertEqual(http.HTTPStatus.OK, response.status_code)
        self.assertTrue(response.streaming)

    def test_download_url(self):
        """Test request_download_file url"""
        i_d = 'abc'
        self.assertEqual(
            f'/drive/download/{i_d}',
            self._get_download_url(i_d)
        )

    def test_download_methods(self):
        """Test request_download_file methods"""
        url = self._get_download_url(str(uuid4()))

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
        self.client.force_login(self.user)
        response = self.client.post(url)
        self.assertEqual(http.HTTPStatus.METHOD_NOT_ALLOWED, response.status_code)

        response = self.client.put(url)
        self.assertEqual(http.HTTPStatus.METHOD_NOT_ALLOWED, response.status_code)

        response = self.client.delete(url)
        self.assertEqual(http.HTTPStatus.METHOD_NOT_ALLOWED, response.status_code)

    def test_download(self):
        """Test request download file"""
        # Prepare SP
        sp_path = os.path.join(self.root_test_dir, 'sp')
        os.makedirs(sp_path, exist_ok=True)
        s_p, root = create_storage_provider_helper(
            'sp1',
            StorageProviderTypeEnum.LOCAL_PATH.value,
            sp_path,
        )
        with open(os.path.join(sp_path, '01 file.txt'), 'w+') as f_h:
            f_h.write('')
        LocalStorageProviderIndexer.sync(root)
        file_obj = LocalFileObject.objects.filter(name='01 file.txt').first()

        # Request invalid file
        self.client.force_login(self.user)
        response = self.client.get(self._get_download_url(str(uuid4())))
        self.assertEqual(http.HTTPStatus.NOT_FOUND, response.status_code)
        # No permission
        response = self.client.get(self._get_download_url(str(file_obj.pk)))
        self.assertEqual(http.HTTPStatus.FORBIDDEN, response.status_code)
        # Request folder
        response = self.client.get(self._get_download_url(str(root.pk)))
        self.assertEqual(http.HTTPStatus.NOT_FOUND, response.status_code)

        # Has permission
        StorageProviderUser.objects.create(
            storage_provider=s_p,
            user=self.user,
            permission=StorageProviderUser.PERMISSION.READ,
        )
        response = self.client.get(self._get_download_url(str(file_obj.pk)))
        self.assertEqual(http.HTTPStatus.OK, response.status_code)
        self.assertTrue(response.streaming)

    def test_create_new_folder(self):
        """Test manage_file (create new folder)"""
        # Prepare SP
        sp_path = os.path.join(self.root_test_dir, 'sp')
        os.makedirs(sp_path, exist_ok=True)
        _, root = create_storage_provider_helper(
            'sp1',
            StorageProviderTypeEnum.LOCAL_PATH.value,
            sp_path,
        )
        with open(os.path.join(sp_path, 'file1.txt'), 'w+') as f_h:
            f_h.write('abc')
        os.makedirs(os.path.join(sp_path, 'fold'))
        LocalStorageProviderIndexer.sync(root)
        file_1 = LocalFileObject.objects.filter(name='file1.txt').first()

        self.client.force_login(self.admin_user)

        # Invalid target
        response = self.client.post(
            self._get_manage_url(str(file_1.pk))+'?action=new-folder',
            dict(name='helloz'),
            content_type=MIMETYPE_JSON
        )
        self.assertEqual(http.HTTPStatus.BAD_REQUEST, response.status_code)
        self.assertEqual(
            dict(error='Only can create folder in a folder!'),
            response.json()
        )

        # Same name with existing
        response = self.client.post(
            self._get_manage_url(str(root.pk))+'?action=new-folder',
            dict(name='fold'),
            content_type=MIMETYPE_JSON
        )
        self.assertEqual(http.HTTPStatus.BAD_REQUEST, response.status_code)
        self.assertEqual(
            dict(error='Sibling already has same name!'),
            response.json()
        )

        # Invalid name
        for name in ['/', './', '../', sp_path, '!?']:
            response = self.client.post(
                self._get_manage_url(str(root.pk))+'?action=new-folder',
                dict(name=name),
                content_type=MIMETYPE_JSON
            )
            self.assertEqual(http.HTTPStatus.BAD_REQUEST, response.status_code)
            self.assertEqual(
                dict(error='Invalid name!'),
                response.json()
            )

        # Valid name
        for name in ['heh', '你豪']:
            response = self.client.post(
                self._get_manage_url(str(root.pk))+'?action=new-folder',
                dict(name=name),
                content_type=MIMETYPE_JSON
            )
            self.assertEqual(http.HTTPStatus.CREATED, response.status_code)
            data = response.json()
            self.assertEqual(name, data['name'])
            self.assertEqual(FileObjectTypeEnum.FOLDER, data['objType'])
            self.assertEqual(name, data['relPath'])
            new_folder = LocalFileObject.objects.get(name=name)
            self.assertEqual(os.path.join(sp_path, name), new_folder.full_path)
            self.assertTrue(os.path.isdir(os.path.join(sp_path, name)))

    def test_create_new_folder_permission(self):
        """Test manage_file (create new folder) - permission"""
        # Prepare SP
        sp_path = os.path.join(self.root_test_dir, 'sp')
        os.makedirs(sp_path, exist_ok=True)
        s_p, root = create_storage_provider_helper(
            'sp1',
            StorageProviderTypeEnum.LOCAL_PATH.value,
            sp_path,
        )
        with open(os.path.join(sp_path, 'file1.txt'), 'w+') as f_h:
            f_h.write('abc')
        os.makedirs(os.path.join(sp_path, 'fold'))
        LocalStorageProviderIndexer.sync(root)

        # Login as normal user
        self.client.force_login(self.user)
        response = self.client.post(
            self._get_manage_url(str(root.pk))+'?action=new-folder',
            dict(name='heh'),
            content_type=MIMETYPE_JSON
        )
        self.assertEqual(http.HTTPStatus.FORBIDDEN, response.status_code)
        self.assertEqual(
            dict(error='No permission to perform the operation!'),
            response.json()
        )

        # Grant read and test again
        StorageProviderUser.objects.create(
            storage_provider=s_p,
            user=self.user,
            permission=StorageProviderUser.PERMISSION.READ,
        )
        response = self.client.post(
            self._get_manage_url(str(root.pk))+'?action=new-folder',
            dict(name='heh'),
            content_type=MIMETYPE_JSON
        )
        self.assertEqual(http.HTTPStatus.FORBIDDEN, response.status_code)
        self.assertEqual(
            dict(error='No permission to perform the operation!'),
            response.json()
        )

        # Grant read write and test again
        StorageProviderUser.objects.filter(
            storage_provider=s_p,
            user=self.user,
        ).update(
            permission=StorageProviderUser.PERMISSION.READ_WRITE,
        )
        response = self.client.post(
            self._get_manage_url(str(root.pk))+'?action=new-folder',
            dict(name='heh'),
            content_type=MIMETYPE_JSON
        )
        self.assertEqual(http.HTTPStatus.CREATED, response.status_code)

    def test_rename(self):
        """Test manage_file (rename)"""
        # Prepare SP
        sp_path = os.path.join(self.root_test_dir, 'sp')
        os.makedirs(sp_path, exist_ok=True)
        _, root = create_storage_provider_helper(
            'sp1',
            StorageProviderTypeEnum.LOCAL_PATH.value,
            sp_path,
        )
        os.makedirs(os.path.join(sp_path, 'fold'))
        with open(os.path.join(sp_path, 'fold', 'file1.txt'), 'w+') as f_h:
            f_h.write('abc')
        with open(os.path.join(sp_path, 'fold', 'file2.txt'), 'w+') as f_h:
            f_h.write('abc')
        LocalStorageProviderIndexer.sync(root)
        file_1 = LocalFileObject.objects.get(name='file1.txt')
        file_2 = LocalFileObject.objects.get(name='file2.txt')
        folder = LocalFileObject.objects.get(name='fold')

        # Invalid name
        self.client.force_login(self.admin_user)
        for name in ['.', '..', './', '.././file1.txt', '?!']:
            response = self.client.post(
                self._get_manage_url(str(file_1.pk))+'?action=rename',
                dict(name=name),
                content_type=MIMETYPE_JSON
            )
            self.assertEqual(http.HTTPStatus.BAD_REQUEST, response.status_code)
            self.assertEqual(
                dict(error='Invalid name!'),
                response.json()
            )

        # Duplicate name
        response = self.client.post(
            self._get_manage_url(str(file_1.pk))+'?action=rename',
            dict(name='file2.txt'),
            content_type=MIMETYPE_JSON
        )
        self.assertEqual(http.HTTPStatus.BAD_REQUEST, response.status_code)
        self.assertEqual(
            dict(error='Sibling already has same name!'),
            response.json()
        )
        file_1.refresh_from_db()
        self.assertEqual('file1.txt', file_1.name)

        # Same name
        response = self.client.post(
            self._get_manage_url(str(file_1.pk))+'?action=rename',
            dict(name=file_1.name),
            content_type=MIMETYPE_JSON
        )
        self.assertEqual(http.HTTPStatus.OK, response.status_code)
        self.assertEqual({}, response.json())
        file_1.refresh_from_db()
        self.assertEqual('file1.txt', file_1.name)

        # Valid name
        response = self.client.post(
            self._get_manage_url(str(file_1.pk))+'?action=rename',
            dict(name='file3.txt'),
            content_type=MIMETYPE_JSON
        )
        self.assertEqual(http.HTTPStatus.OK, response.status_code)
        self.assertEqual({}, response.json())
        file_1.refresh_from_db()
        self.assertEqual('file3.txt', file_1.name)
        self.assertEqual(os.path.join(folder.full_path, 'file3.txt'), file_1.full_path)
        self.assertTrue(os.path.isfile(file_1.full_path))

        # Rename folder
        response = self.client.post(
            self._get_manage_url(str(folder.pk))+'?action=rename',
            dict(name='XD'),
            content_type=MIMETYPE_JSON
        )
        self.assertEqual(http.HTTPStatus.OK, response.status_code)
        self.assertEqual({}, response.json())
        self.assertFalse(os.path.exists(os.path.join(root.full_path, 'fold')))
        self.assertTrue(os.path.exists(os.path.join(root.full_path, 'XD')))

        folder.refresh_from_db()
        self.assertEqual('XD', folder.name)
        self.assertEqual(os.path.join(root.full_path, 'XD'), folder.full_path)

        file_1.refresh_from_db()
        self.assertEqual(os.path.join(folder.full_path, file_1.name), file_1.full_path)
        file_2.refresh_from_db()
        self.assertEqual(os.path.join(folder.full_path, file_2.name), file_2.full_path)

    def test_rename_permission(self):
        """Test manage_file (rename) permission"""
        # Prepare SP
        sp_path = os.path.join(self.root_test_dir, 'sp')
        os.makedirs(sp_path, exist_ok=True)
        s_p, root = create_storage_provider_helper(
            'sp1',
            StorageProviderTypeEnum.LOCAL_PATH.value,
            sp_path,
        )
        os.makedirs(os.path.join(sp_path, 'fold'))
        with open(os.path.join(sp_path, 'fold', 'file1.txt'), 'w+') as f_h:
            f_h.write('abc')
        LocalStorageProviderIndexer.sync(root)
        file_1 = LocalFileObject.objects.get(name='file1.txt')
        folder = LocalFileObject.objects.get(name='fold')
        self.client.force_login(self.user)

        # Valid name
        response = self.client.post(
            self._get_manage_url(str(file_1.pk))+'?action=rename',
            dict(name='file3.txt'),
            content_type=MIMETYPE_JSON
        )
        self.assertEqual(http.HTTPStatus.FORBIDDEN, response.status_code)
        self.assertEqual(
            dict(error='No permission to perform the operation!'),
            response.json()
        )
        self.assertFalse(os.path.exists(os.path.join(folder.full_path, 'file3.txt')))

        # Grant READ permission & try again
        StorageProviderUser.objects.create(
            storage_provider=s_p,
            user=self.user,
            permission=StorageProviderUser.PERMISSION.READ,
        )
        response = self.client.post(
            self._get_manage_url(str(file_1.pk))+'?action=rename',
            dict(name='file3.txt'),
            content_type=MIMETYPE_JSON
        )
        self.assertEqual(http.HTTPStatus.FORBIDDEN, response.status_code)
        self.assertEqual(
            dict(error='No permission to perform the operation!'),
            response.json()
        )
        self.assertFalse(os.path.exists(os.path.join(folder.full_path, 'file3.txt')))

        # Grant READ-WRITE permission & try again
        StorageProviderUser.objects.filter(
            storage_provider=s_p,
            user=self.user,
        ).update(
            permission=StorageProviderUser.PERMISSION.READ_WRITE
        )
        response = self.client.post(
            self._get_manage_url(str(file_1.pk))+'?action=rename',
            dict(name='file3.txt'),
            content_type=MIMETYPE_JSON
        )
        self.assertEqual(http.HTTPStatus.OK, response.status_code)
        self.assertEqual({}, response.json())
        self.assertTrue(os.path.exists(os.path.join(folder.full_path, 'file3.txt')))

    def test_delete(self):
        """Test manage_file (delete)"""
        # Prepare SP
        sp_path = os.path.join(self.root_test_dir, 'sp')
        os.makedirs(sp_path, exist_ok=True)
        _, root = create_storage_provider_helper(
            'sp1',
            StorageProviderTypeEnum.LOCAL_PATH.value,
            sp_path,
        )
        os.makedirs(os.path.join(sp_path, 'fold'))
        with open(os.path.join(sp_path, 'file1.txt'), 'w+') as f_h:
            f_h.write('abc')
        with open(os.path.join(sp_path, 'fold', 'file2.txt'), 'w+') as f_h:
            f_h.write('abc')
        LocalStorageProviderIndexer.sync(root)
        file_1 = LocalFileObject.objects.get(name='file1.txt')
        folder = LocalFileObject.objects.get(name='fold')
        self.client.force_login(self.admin_user)

        # Invalid ID
        response = self.client.delete(self._get_manage_url(str(uuid4())))
        self.assertEqual(http.HTTPStatus.NOT_FOUND, response.status_code)
        self.assertEqual(dict(error='Object not found'), response.json())

        # Valid file
        response = self.client.delete(self._get_manage_url(str(file_1.pk)))
        self.assertEqual(http.HTTPStatus.OK, response.status_code)
        self.assertEqual({}, response.json())
        self.assertFalse(LocalFileObject.objects.filter(name='file1.txt').exists())
        self.assertFalse(os.path.exists(os.path.join(sp_path, 'file1.txt')))
        self.assertTrue(os.path.exists(os.path.join(sp_path, 'fold')))

        # Valid folder
        response = self.client.delete(self._get_manage_url(str(folder.pk)))
        self.assertEqual(http.HTTPStatus.OK, response.status_code)
        self.assertEqual({}, response.json())
        self.assertFalse(LocalFileObject.objects.filter(name='fold').exists())
        self.assertFalse(LocalFileObject.objects.filter(name='file2.txt').exists())
        self.assertFalse(os.path.exists(os.path.join(sp_path, 'fold')))

    def test_delete_permission(self):
        """Test manage_file (delete) - Permission"""
        # Prepare SP
        sp_path = os.path.join(self.root_test_dir, 'sp')
        os.makedirs(sp_path, exist_ok=True)
        s_p, root = create_storage_provider_helper(
            'sp1',
            StorageProviderTypeEnum.LOCAL_PATH.value,
            sp_path,
        )
        with open(os.path.join(sp_path, 'file1.txt'), 'w+') as f_h:
            f_h.write('abc')
        LocalStorageProviderIndexer.sync(root)
        file_1 = LocalFileObject.objects.get(name='file1.txt')
        self.client.force_login(self.user)

        # Invalid ID
        response = self.client.delete(self._get_manage_url(str(uuid4())))
        self.assertEqual(http.HTTPStatus.NOT_FOUND, response.status_code)
        self.assertEqual(dict(error='Object not found'), response.json())

        # Valid file - No permission
        response = self.client.delete(self._get_manage_url(str(file_1.pk)))
        self.assertEqual(http.HTTPStatus.FORBIDDEN, response.status_code)
        self.assertEqual(
            dict(error='No permission to perform the operation!'),
            response.json()
        )
        self.assertTrue(LocalFileObject.objects.filter(name='file1.txt').exists())
        self.assertTrue(os.path.exists(os.path.join(sp_path, 'file1.txt')))

        # Valid file - READ permission
        StorageProviderUser.objects.create(
            storage_provider=s_p,
            user=self.user,
            permission=StorageProviderUser.PERMISSION.READ,
        )
        response = self.client.delete(self._get_manage_url(str(file_1.pk)))
        self.assertEqual(http.HTTPStatus.FORBIDDEN, response.status_code)
        self.assertEqual(
            dict(error='No permission to perform the operation!'),
            response.json()
        )

        # Valid file - READ_WRITE permission
        StorageProviderUser.objects.filter(
            storage_provider=s_p,
            user=self.user,
        ).update(
            permission=StorageProviderUser.PERMISSION.READ_WRITE
        )
        response = self.client.delete(self._get_manage_url(str(file_1.pk)))
        self.assertEqual(http.HTTPStatus.OK, response.status_code)
        self.assertEqual({}, response.json())
        self.assertFalse(LocalFileObject.objects.filter(name='file1.txt').exists())
        self.assertFalse(os.path.exists(os.path.join(sp_path, 'file1.txt')))

    def test_create_files(self):
        """Test manage_file (create_files)"""
        # Prepare data
        test_path = os.path.join(self.root_test_dir, 'sp')
        os.makedirs(test_path, exist_ok=True)

        # Prepare SP
        sp_path = os.path.join(test_path, 'gg')
        _, root = create_storage_provider_helper(
            'sp1',
            StorageProviderTypeEnum.LOCAL_PATH.value,
            sp_path,
        )
        os.makedirs(os.path.join(sp_path, 'fold'))
        with open(os.path.join(sp_path, 'fold', 'this-iz-file.txt'), 'w+') as f_h:
            f_h.write('def')
        LocalStorageProviderIndexer.sync(root)
        folder = LocalFileObject.objects.get(name='fold')
        file_1 = LocalFileObject.objects.get(name='this-iz-file.txt')
        self.client.force_login(self.admin_user)
        ul_file = SimpleUploadedFile('lel.txt', b'abc')
        ul_file_2 = SimpleUploadedFile('this-iz-file.txt', b'heh')

        # Upload file (invalid dest)
        response = self.client.post(
            self._get_manage_url(str(file_1.pk)) + '?action=new-files',
            dict(files=ul_file)
        )
        self.assertEqual(http.HTTPStatus.BAD_REQUEST, response.status_code)
        self.assertEqual(dict(error='Destination must be a folder!'), response.json())

        # Upload no file
        response = self.client.post(self._get_manage_url(str(folder.pk)) + '?action=new-files')
        self.assertEqual(http.HTTPStatus.BAD_REQUEST, response.status_code)
        self.assertEqual(dict(error='No file was uploaded.'), response.json())

        # Upload file
        response = self.client.post(
            self._get_manage_url(str(root.pk)) + '?action=new-files',
            dict(
                files=ul_file,
                paths=['lel.txt'],
            )
        )
        self.assertEqual(http.HTTPStatus.CREATED, response.status_code)
        self.assertEqual({}, response.json())
        self.assertTrue(os.path.exists(os.path.join(root.full_path, 'lel.txt')))
        self.assertEqual(
            os.path.join(root.full_path, 'lel.txt'),
            LocalFileObject.objects.get(name='lel.txt').full_path,
        )

        # Upload folder (merge with existing)
        response = self.client.post(
            self._get_manage_url(str(root.pk)) + '?action=new-files',
            dict(
                files=ul_file_2,
                paths=['fold/this-iz-file.txt'],
            )
        )
        self.assertEqual(http.HTTPStatus.CREATED, response.status_code)
        self.assertEqual({}, response.json())
        ul_f1_path = os.path.join(root.full_path, 'fold', 'this-iz-file.txt')
        ul_f2_path = os.path.join(root.full_path, 'fold', 'this-iz-file (1).txt')
        self.assertTrue(os.path.exists(ul_f1_path))
        self.assertTrue(os.path.exists(ul_f2_path))

        # Upload folder (auto create new folder)
        response = self.client.post(
            self._get_manage_url(str(root.pk)) + '?action=new-files',
            dict(
                files=ul_file_2,
                paths=['XD/this-iz-file.txt'],
            )
        )
        self.assertEqual(http.HTTPStatus.CREATED, response.status_code)
        self.assertEqual({}, response.json())
        ul_f2_path = os.path.join(root.full_path, 'XD', 'this-iz-file.txt')
        self.assertTrue(os.path.exists(ul_f2_path))

    def test_create_files_permission(self):
        """Test manage_file (create_files) - Permission"""
        # Prepare SP
        sp_path = os.path.join(self.root_test_dir, 'sp')
        os.makedirs(sp_path)
        s_p, root = create_storage_provider_helper(
            'anya',
            StorageProviderTypeEnum.LOCAL_PATH.value,
            sp_path,
        )
        LocalStorageProviderIndexer.sync(root)
        self.client.force_login(self.user)
        ul_file = SimpleUploadedFile('lel.txt', b'abc')

        # No permission
        response = self.client.post(
            self._get_manage_url(str(root.pk)) + '?action=new-files',
            dict(
                files=ul_file,
                paths=['lel.txt'],
            )
        )
        self.assertEqual(http.HTTPStatus.FORBIDDEN, response.status_code)
        self.assertEqual(
            dict(error='No permission to perform the operation!'),
            response.json()
        )
        self.assertEqual(1, LocalFileObject.objects.count())
        self.assertFalse(os.path.exists(os.path.join(root.full_path, 'lel.txt')))

        # With READ permission
        StorageProviderUser.objects.create(
            storage_provider=s_p,
            user=self.user,
            permission=StorageProviderUser.PERMISSION.READ,
        )
        response = self.client.post(
            self._get_manage_url(str(root.pk)) + '?action=new-files',
            dict(
                files=ul_file,
                paths=['lel.txt'],
            )
        )
        self.assertEqual(http.HTTPStatus.FORBIDDEN, response.status_code)
        self.assertEqual(
            dict(error='No permission to perform the operation!'),
            response.json()
        )
        self.assertEqual(1, LocalFileObject.objects.count())
        self.assertFalse(os.path.exists(os.path.join(root.full_path, 'lel.txt')))

        # With READ_WRITE permission
        StorageProviderUser.objects.filter(
            storage_provider=s_p,
            user=self.user,
        ).update(
            permission=StorageProviderUser.PERMISSION.READ_WRITE,
        )
        response = self.client.post(
            self._get_manage_url(str(root.pk)) + '?action=new-files',
            dict(
                files=ul_file,
                paths=['lel.txt'],
            )
        )
        self.assertEqual(http.HTTPStatus.CREATED, response.status_code)
        self.assertEqual({}, response.json())
        self.assertEqual(2, LocalFileObject.objects.count())
        self.assertTrue(os.path.exists(os.path.join(root.full_path, 'lel.txt')))

    def test_get_file(self):
        """Test manage_file (Get)"""
        # Prepare SP
        sp_path = os.path.join(self.root_test_dir, 'sp')
        os.makedirs(sp_path)
        s_p, root = create_storage_provider_helper(
            'anya',
            StorageProviderTypeEnum.LOCAL_PATH.value,
            sp_path,
        )
        folder_path = os.path.join(sp_path, 'fold')
        os.makedirs(folder_path)
        shutil.copy2(os.path.join('samples', 'sample.jpg'), folder_path)
        shutil.copy2(os.path.join('samples', 'sample.m4a'), folder_path)
        LocalStorageProviderIndexer.sync(root)
        folder = LocalFileObject.objects.get(name='fold')
        picture = LocalFileObject.objects.get(name='sample.jpg')
        music = LocalFileObject.objects.get(name='sample.m4a')
        self.client.force_login(self.admin_user)

        # Test folder entity
        response = self.client.get(
            self._get_manage_url(str(folder.pk)),
            dict(
                action='entity',
                traceParents='true',
                traceChildren='true',
                traceStorageProvider='true',
                metadata='true',
            )
        )
        self.assertEqual(http.HTTPStatus.OK, response.status_code)
        data = response.json()
        del data['lastModified']
        del data['size']
        for child in data['children']:
            del child['lastModified']
            del child['size']
        expected_data = dict(
            id=str(folder.pk),
            name='fold',
            objType=FileObjectTypeEnum.FOLDER.value,
            relPath='fold',
            extension=None,
            type=None,
            parent=dict(
                id=str(root.pk),
                name='anya',
                objType=FileObjectTypeEnum.FOLDER.value,
            ),
            storageProvider=dict(
                id=s_p.pk,
                name='anya',
                path=s_p.path,
            ),
            metadata={},
            trace=[
                dict(
                    id=str(root.pk),
                    name='anya',
                    objType=FileObjectTypeEnum.FOLDER.value,
                ),
            ],
            children=[
                dict(
                    id=str(picture.pk),
                    name='sample.jpg',
                    objType=FileObjectTypeEnum.FILE.value,
                    relPath='fold/sample.jpg',
                    extension='jpg',
                    type='picture',
                    parent=dict(
                        id=str(folder.pk),
                        name='fold',
                        objType=FileObjectTypeEnum.FILE.value
                    ),
                ),
                dict(
                    id=str(music.pk),
                    name='sample.m4a',
                    objType=FileObjectTypeEnum.FILE.value,
                    relPath='fold/sample.m4a',
                    extension='m4a',
                    type='music',
                    parent=dict(
                        id=str(folder.pk),
                        name='fold',
                        objType=FileObjectTypeEnum.FILE.value
                    ),
                )
            ]
        )
        self.assertEqual(expected_data, data)

        # Test file entity
        response = self.client.get(
            self._get_manage_url(str(music.pk)),
            dict(action='entity', metadata='true')
        )
        self.assertEqual(http.HTTPStatus.OK, response.status_code)
        data = response.json()
        del data['lastModified']
        del data['size']
        data['metadata'] = {
            key: value for key, value in data['metadata'].items() if\
                key in {'title', 'album', 'artist'}
        }
        expected_data = dict(
            id=str(music.pk),
            name='sample.m4a',
            objType=FileObjectTypeEnum.FILE.value,
            relPath='fold/sample.m4a',
            extension='m4a',
            type='music',
            parent=dict(
                id=str(folder.pk),
                name='fold',
                objType=FileObjectTypeEnum.FILE.value,
            ),
            metadata=dict(
                title='lollipop',
                album='anya',
                artist='ice cream',
            ),
        )
        self.assertEqual(expected_data, data)

        # Test get album image
        response = self.client.get(
            self._get_manage_url(str(music.pk)),
            dict(action='album-image')
        )
        self.assertEqual(http.HTTPStatus.OK, response.status_code)
        self.assertGreater(len(response.content), 0)

        # Test get picture metadata
        response = self.client.get(
            self._get_manage_url(str(picture.pk)),
            dict(action='metadata')
        )
        self.assertEqual(http.HTTPStatus.OK, response.status_code)
        self.assertEqual({}, response.json())

        # Test get music metadata
        response = self.client.get(
            self._get_manage_url(str(music.pk)),
            dict(action='metadata')
        )
        self.assertEqual(http.HTTPStatus.OK, response.status_code)
        data = response.json()
        self.assertEqual('lollipop', data['title'])
        self.assertEqual('anya', data['album'])
        self.assertEqual('ice cream', data['artist'])

    def test_get_file_permission(self):
        """Test manage_file (Get) - Permission"""
        # Prepare SP
        sp_path = os.path.join(self.root_test_dir, 'sp')
        os.makedirs(sp_path)
        s_p, root = create_storage_provider_helper(
            'anya',
            StorageProviderTypeEnum.LOCAL_PATH.value,
            sp_path,
        )
        with open(os.path.join(sp_path, 'peanutz.txt'), 'w+') as f_h:
            f_h.write('where is season 3')
        LocalStorageProviderIndexer.sync(root)
        file_1 = LocalFileObject.objects.get(name='peanutz.txt')
        self.client.force_login(self.user)

        # Get (no permission)
        response = self.client.get(self._get_manage_url(str(file_1.pk)))
        self.assertEqual(http.HTTPStatus.FORBIDDEN, response.status_code)
        self.assertEqual(
            dict(error='No permission to perform the operation!'),
            response.json()
        )

        # Get (READ permission)
        StorageProviderUser.objects.create(
            storage_provider=s_p,
            user=self.user,
            permission=StorageProviderUser.PERMISSION.READ
        )
        response = self.client.get(self._get_manage_url(str(file_1.pk)) + '?action=metadata')
        self.assertEqual(http.HTTPStatus.OK, response.status_code)
        self.assertEqual({}, response.json())
