import http

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from drive.cache import ModelCache
from drive.core.storage_provider import create_storage_provider_helper
from drive.models import (
    Job,
    LocalFileObject,
    StorageProvider,
    StorageProviderUser,
    StorageProviderTypeEnum,
)
from drive.tests.web.shared import MIMETYPE_JSON

class TestStorageProvider(TestCase): # pylint: disable=too-many-public-methods
    """Test storage provider views"""

    def _get_manage_url(self, i_d: int):
        return reverse('storage-provider.manage', args=[i_d])

    def _get_index_url(self, i_d: int):
        return reverse('storage-provider.index', args=[i_d])

    def setUp(self):
        ModelCache.disable()
        self.get_types_url = reverse('storage_provider.list_types')
        self.get_permissions_url = reverse('storage-provider.list_permissions')
        self.list_url = reverse('storage-provider.list')
        self.create_url = reverse('storage-provider.create')

    def tearDown(self):
        ModelCache.enable()
        StorageProvider.objects.all().delete()
        User.objects.all().delete()
        Job.objects.all().delete()

    def test_get_types_url(self):
        """Test get_sp_types url"""
        self.assertEqual(
            '/drive/web-api/storage-provider-types',
            self.get_types_url
        )

    def test_get_types_methods(self):
        """Test get_sp_types methods"""
        response = self.client.post(self.get_types_url)
        self.assertEqual(http.HTTPStatus.METHOD_NOT_ALLOWED, response.status_code)
        response = self.client.put(self.get_types_url)
        self.assertEqual(http.HTTPStatus.METHOD_NOT_ALLOWED, response.status_code)
        response = self.client.delete(self.get_types_url)
        self.assertEqual(http.HTTPStatus.METHOD_NOT_ALLOWED, response.status_code)

    def test_get_types(self):
        """Test get_sp_types"""
        response = self.client.get(self.get_types_url)
        self.assertEqual(http.HTTPStatus.OK, response.status_code)
        self.assertEqual(dict(
            values=[
                dict(
                    name='Local Storage',
                    value='LOCAL_PATH',
                ),
            ],
        ), response.json())

    def test_get_permissions_url(self):
        """Test get_sp_permissions url"""
        self.assertEqual(
            '/drive/web-api/storage-provider-permissions',
            self.get_permissions_url
        )

    def test_get_permissions_methods(self):
        """Test get_sp_permissions methods"""
        response = self.client.get(self.get_permissions_url)
        self.assertEqual(http.HTTPStatus.UNAUTHORIZED, response.status_code)
        response = self.client.post(self.get_permissions_url)
        self.assertEqual(http.HTTPStatus.UNAUTHORIZED, response.status_code)
        response = self.client.put(self.get_permissions_url)
        self.assertEqual(http.HTTPStatus.UNAUTHORIZED, response.status_code)
        response = self.client.delete(self.get_permissions_url)
        self.assertEqual(http.HTTPStatus.UNAUTHORIZED, response.status_code)

        self.client.force_login(User.objects.create_user('lalala'))
        response = self.client.post(self.get_permissions_url)
        self.assertEqual(http.HTTPStatus.METHOD_NOT_ALLOWED, response.status_code)
        response = self.client.put(self.get_permissions_url)
        self.assertEqual(http.HTTPStatus.METHOD_NOT_ALLOWED, response.status_code)
        response = self.client.delete(self.get_permissions_url)
        self.assertEqual(http.HTTPStatus.METHOD_NOT_ALLOWED, response.status_code)

    def test_get_permissions(self):
        """Test get_sp_permissions"""
        self.client.force_login(User.objects.create_user('lalala'))

        response = self.client.get(self.get_permissions_url)
        self.assertEqual(http.HTTPStatus.OK, response.status_code)
        self.assertEqual(dict(
            values=[
                dict(
                    name='None',
                    value=0,
                ),
                dict(
                    name='Read',
                    value=10,
                ),
                dict(
                    name='Read & Write',
                    value=20,
                ),
            ],
        ), response.json())

    def test_list_url(self):
        """Tets get_storage_providers url"""
        self.assertEqual('/drive/web-api/storage-providers', self.list_url)

    def test_list_methods(self):
        """Test get_storage_providers methods"""
        response = self.client.get(self.list_url)
        self.assertEqual(http.HTTPStatus.UNAUTHORIZED, response.status_code)
        response = self.client.post(self.list_url)
        self.assertEqual(http.HTTPStatus.UNAUTHORIZED, response.status_code)
        response = self.client.put(self.list_url)
        self.assertEqual(http.HTTPStatus.UNAUTHORIZED, response.status_code)
        response = self.client.delete(self.list_url)
        self.assertEqual(http.HTTPStatus.UNAUTHORIZED, response.status_code)

        self.client.force_login(User.objects.create_user('lalala'))
        response = self.client.post(self.list_url)
        self.assertEqual(http.HTTPStatus.METHOD_NOT_ALLOWED, response.status_code)
        response = self.client.put(self.list_url)
        self.assertEqual(http.HTTPStatus.METHOD_NOT_ALLOWED, response.status_code)
        response = self.client.delete(self.list_url)
        self.assertEqual(http.HTTPStatus.METHOD_NOT_ALLOWED, response.status_code)

    def test_list(self):
        """Test get_storage_providers"""
        # Create some sp & users
        sp_a, root_a = create_storage_provider_helper(
            'spA',
            StorageProviderTypeEnum.LOCAL_PATH.value,
            '/var'
        )
        sp_b, root_b = create_storage_provider_helper(
            'spB',
            StorageProviderTypeEnum.LOCAL_PATH.value,
            '/lib'
        )
        sp_c, root_c = create_storage_provider_helper(
            'spC',
            StorageProviderTypeEnum.LOCAL_PATH.value,
            '/usr'
        )
        admin_user = User.objects.create_superuser('lalala')
        normal_user = User.objects.create_user('norm')

        # normal user can only access after granted, admin can access regardless.
        StorageProviderUser.objects.create(
            storage_provider=sp_a,
            user=normal_user,
            permission=StorageProviderUser.PERMISSION.READ,
        )
        StorageProviderUser.objects.create(
            storage_provider=sp_b,
            user=normal_user,
            permission=StorageProviderUser.PERMISSION.READ_WRITE,
        )
        StorageProviderUser.objects.create(
            storage_provider=sp_c,
            user=admin_user,
            permission=StorageProviderUser.PERMISSION.NONE,
        )

        # Test as admin user
        self.client.force_login(admin_user)
        response = self.client.get(self.list_url)
        self.assertEqual(http.HTTPStatus.OK, response.status_code)
        received_data = response.json()
        for entry in received_data['values']:
            self.assertTrue('usedSpace' in entry)
            del entry['usedSpace']
            self.assertTrue('totalSpace' in entry)
            del entry['totalSpace']
        expected_data = dict(
            values=[
                dict(
                    id=sp_a.pk,
                    name=sp_a.name,
                    type=sp_a.type,
                    path=sp_a.path,
                    rootFolder=str(root_a.pk),
                    indexing=True,
                    permissions=[],
                ),
                dict(
                    id=sp_b.pk,
                    name=sp_b.name,
                    type=sp_b.type,
                    path=sp_b.path,
                    rootFolder=str(root_b.pk),
                    indexing=True,
                    permissions=[],
                ),
                dict(
                    id=sp_c.pk,
                    name=sp_c.name,
                    type=sp_c.type,
                    path=sp_c.path,
                    rootFolder=str(root_c.pk),
                    indexing=True,
                    permissions=[],
                ),
            ]
        )
        self.assertEqual(expected_data, received_data)

        # Test as normal user
        self.client.force_login(normal_user)
        response = self.client.get(self.list_url)
        self.assertEqual(http.HTTPStatus.OK, response.status_code)
        received_data = response.json()
        for entry in received_data['values']:
            self.assertTrue('usedSpace' in entry)
            del entry['usedSpace']
            self.assertTrue('totalSpace' in entry)
            del entry['totalSpace']
        expected_data = dict(
            values=[
                dict(
                    id=sp_a.pk,
                    name=sp_a.name,
                    type=sp_a.type,
                    path=sp_a.path,
                    rootFolder=str(root_a.pk),
                    indexing=True,
                    permissions=[],
                ),
                dict(
                    id=sp_b.pk,
                    name=sp_b.name,
                    type=sp_b.type,
                    path=sp_b.path,
                    rootFolder=str(root_b.pk),
                    indexing=True,
                    permissions=[],
                ),
            ]
        )
        self.assertEqual(expected_data, received_data)

    def test_create_url(self):
        """Tets create_storage_provider url"""
        self.assertEqual(
            '/drive/web-api/storage-providers/create',
            self.create_url
        )

    def test_create_methods(self):
        """Test create_storage_provider methods"""
        response = self.client.get(self.create_url)
        self.assertEqual(http.HTTPStatus.UNAUTHORIZED, response.status_code)
        response = self.client.post(self.create_url)
        self.assertEqual(http.HTTPStatus.UNAUTHORIZED, response.status_code)
        response = self.client.put(self.create_url)
        self.assertEqual(http.HTTPStatus.UNAUTHORIZED, response.status_code)
        response = self.client.delete(self.create_url)
        self.assertEqual(http.HTTPStatus.UNAUTHORIZED, response.status_code)

        self.client.force_login(User.objects.create_user('lalala'))
        response = self.client.get(self.create_url)
        self.assertEqual(http.HTTPStatus.METHOD_NOT_ALLOWED, response.status_code)
        response = self.client.post(self.create_url)
        self.assertEqual(http.HTTPStatus.UNAUTHORIZED, response.status_code)
        response = self.client.put(self.create_url)
        self.assertEqual(http.HTTPStatus.METHOD_NOT_ALLOWED, response.status_code)
        response = self.client.delete(self.create_url)
        self.assertEqual(http.HTTPStatus.METHOD_NOT_ALLOWED, response.status_code)

        self.client.force_login(User.objects.create_superuser('anya'))
        response = self.client.get(self.create_url)
        self.assertEqual(http.HTTPStatus.METHOD_NOT_ALLOWED, response.status_code)
        response = self.client.put(self.create_url)
        self.assertEqual(http.HTTPStatus.METHOD_NOT_ALLOWED, response.status_code)
        response = self.client.delete(self.create_url)
        self.assertEqual(http.HTTPStatus.METHOD_NOT_ALLOWED, response.status_code)

    def test_create(self):
        """Test create_storage_provider"""
        admin_user = User.objects.create_superuser('lalala')
        self.client.force_login(admin_user)

        # Test invalid name
        post_data = dict(
            name='',
            type=StorageProviderTypeEnum.LOCAL_PATH,
            path='/var',
        )
        response = self.client.post(
            self.create_url,
            post_data,
            content_type=MIMETYPE_JSON,
        )
        self.assertEqual(http.HTTPStatus.BAD_REQUEST, response.status_code)

        # Test invalid type
        post_data = dict(
            name='var',
            type='unknown...',
            path='/var',
        )
        response = self.client.post(
            self.create_url,
            post_data,
            content_type=MIMETYPE_JSON,
        )
        self.assertEqual(http.HTTPStatus.BAD_REQUEST, response.status_code)

        # Test invalid path
        post_data = dict(
            name='hehe',
            type=StorageProviderTypeEnum.LOCAL_PATH,
            path='/@91;a',
        )
        response = self.client.post(
            self.create_url,
            post_data,
            content_type=MIMETYPE_JSON,
        )
        self.assertEqual(http.HTTPStatus.BAD_REQUEST, response.status_code)
        self.assertEqual(
            dict(error=f'Path {post_data["path"]} doesn\'t exist!'),
            response.json()
        )

        # Test valid
        post_data = dict(
            name='var-lib',
            type=StorageProviderTypeEnum.LOCAL_PATH.value,
            path='/var/lib/',
        )
        response = self.client.post(
            self.create_url,
            post_data,
            content_type=MIMETYPE_JSON,
        )
        post_data['path'] = post_data['path'][:-1] # Strip off /
        self.assertEqual(http.HTTPStatus.CREATED, response.status_code)
        s_p = StorageProvider.objects.first()
        self.assertEqual(post_data['name'], s_p.name)
        self.assertEqual(post_data['type'], s_p.type)
        self.assertEqual(post_data['path'], s_p.path)
        self.assertTrue(s_p.indexing)
        root_folder = LocalFileObject.objects.first()
        self.assertEqual(s_p, root_folder.storage_provider)
        expected_data = dict(
            id=s_p.pk,
            name=post_data['name'],
            type=post_data['type'],
            path=post_data['path'],
            rootFolder=str(root_folder.pk),
            indexing=True,
            permissions=[],
        )
        received_data = response.json()
        self.assertTrue('usedSpace' in received_data)
        del received_data['usedSpace']
        self.assertTrue('totalSpace' in received_data)
        del received_data['totalSpace']
        self.assertEqual(expected_data, received_data)

        # Test same name
        post_data = dict(
            name='var-lib',
            type=StorageProviderTypeEnum.LOCAL_PATH.value,
            path='/usr',
        )
        response = self.client.post(
            self.create_url,
            post_data,
            content_type=MIMETYPE_JSON,
        )
        self.assertEqual(http.HTTPStatus.BAD_REQUEST, response.status_code)
        self.assertEqual(dict(error='Name is already in use!'), response.json())

        # Test same path
        post_data = dict(
            name='var2',
            type=StorageProviderTypeEnum.LOCAL_PATH.value,
            path='/var/lib',
        )
        response = self.client.post(
            self.create_url,
            post_data,
            content_type=MIMETYPE_JSON,
        )
        self.assertEqual(http.HTTPStatus.BAD_REQUEST, response.status_code)
        self.assertEqual(dict(error='Path is already added.'), response.json())

        # Test parent path
        post_data = dict(
            name='var2',
            type=StorageProviderTypeEnum.LOCAL_PATH.value,
            path='/var',
        )
        response = self.client.post(
            self.create_url,
            post_data,
            content_type=MIMETYPE_JSON,
        )
        self.assertEqual(http.HTTPStatus.BAD_REQUEST, response.status_code)
        self.assertEqual(
            dict(
                error="""Child path /var/lib is already added, """
                """perhaps update existing provider instead?"""
            ),
            response.json()
        )

        # Test child path
        post_data = dict(
            name='var2',
            type=StorageProviderTypeEnum.LOCAL_PATH.value,
            path='/var/lib/misc',
        )
        response = self.client.post(
            self.create_url,
            post_data,
            content_type=MIMETYPE_JSON,
        )
        self.assertEqual(http.HTTPStatus.BAD_REQUEST, response.status_code)
        self.assertEqual(
            dict(
                error="""Parent path /var/lib is already added, """
                """so the files in this path already exist."""
            ),
            response.json()
        )

    def test_perform_index_url(self):
        """Test perform_index url"""
        self.assertEqual(
            '/drive/web-api/storage-providers/123/index',
            self._get_index_url(123)
        )

    def test_perform_index_methods(self):
        """Test perform_index methods"""
        index_url = self._get_index_url(123)
        response = self.client.get(index_url)
        self.assertEqual(http.HTTPStatus.UNAUTHORIZED, response.status_code)
        response = self.client.post(index_url)
        self.assertEqual(http.HTTPStatus.UNAUTHORIZED, response.status_code)
        response = self.client.put(index_url)
        self.assertEqual(http.HTTPStatus.UNAUTHORIZED, response.status_code)
        response = self.client.delete(index_url)
        self.assertEqual(http.HTTPStatus.UNAUTHORIZED, response.status_code)

        self.client.force_login(User.objects.create_user('lalala'))
        response = self.client.get(index_url)
        self.assertEqual(http.HTTPStatus.METHOD_NOT_ALLOWED, response.status_code)
        response = self.client.put(index_url)
        self.assertEqual(http.HTTPStatus.METHOD_NOT_ALLOWED, response.status_code)
        response = self.client.delete(index_url)
        self.assertEqual(http.HTTPStatus.METHOD_NOT_ALLOWED, response.status_code)

    def test_perform_index(self): # pylint: disable=too-many-statements
        """Test perform_index"""
        s_p, _ = create_storage_provider_helper(
            'name', StorageProviderTypeEnum.LOCAL_PATH.value,
            '/var',
        )
        index_url = self._get_index_url(s_p.pk)
        fail_index_url = self._get_index_url(s_p.id + 100)
        admin_user = User.objects.create_superuser('admin')
        normal_user = User.objects.create_user('normal')

        # Test login as admin
        s_p.indexing = False
        s_p.save()
        self.client.force_login(admin_user)
        # Test invalid ID
        response = self.client.post(fail_index_url)
        self.assertEqual(http.HTTPStatus.NOT_FOUND, response.status_code)
        # Test correct
        response = self.client.post(index_url)
        self.assertEqual(http.HTTPStatus.OK, response.status_code)
        s_p.refresh_from_db()
        self.assertTrue(s_p.indexing)
        self.assertEqual(1, Job.objects.count())
        job = Job.objects.first()
        self.assertEqual(Job.TaskTypes.INDEX, job.task_type)
        self.assertEqual(f'Perform indexing on {s_p.path}', job.description)
        self.assertEqual(str(s_p.pk), job.data)
        Job.objects.all().delete()
        # Test request when indexing
        response = self.client.post(index_url)
        self.assertEqual(http.HTTPStatus.OK, response.status_code)
        self.assertEqual(0, Job.objects.count())

        # Test login as normal user (No permission)
        s_p.indexing = False
        s_p.save()
        self.client.force_login(normal_user)
        # Test invalid ID
        response = self.client.post(fail_index_url)
        self.assertEqual(http.HTTPStatus.NOT_FOUND, response.status_code)
        response = self.client.post(index_url)
        self.assertEqual(http.HTTPStatus.FORBIDDEN, response.status_code)
        s_p.refresh_from_db()
        self.assertFalse(s_p.indexing)

        # Test login as normal user (Read-Only permission)
        sp_p = StorageProviderUser.objects.create(
            storage_provider=s_p, user=normal_user,
            permission=StorageProviderUser.PERMISSION.READ,
        )

        response = self.client.post(index_url)
        self.assertEqual(http.HTTPStatus.FORBIDDEN, response.status_code)
        s_p.refresh_from_db()
        self.assertFalse(s_p.indexing)

        # Test login as normal user (Read-Write permission)
        sp_p.permission = StorageProviderUser.PERMISSION.READ_WRITE
        sp_p.save()
        response = self.client.post(index_url)
        self.assertEqual(http.HTTPStatus.OK, response.status_code)
        s_p.refresh_from_db()
        self.assertTrue(s_p.indexing)
        self.assertEqual(1, Job.objects.count())
        job = Job.objects.first()
        self.assertEqual(Job.TaskTypes.INDEX, job.task_type)
        self.assertEqual(f'Perform indexing on {s_p.path}', job.description)
        self.assertEqual(str(s_p.pk), job.data)
        Job.objects.all().delete()
        # Test request when indexing
        response = self.client.post(index_url)
        self.assertEqual(http.HTTPStatus.OK, response.status_code)
        self.assertEqual(0, Job.objects.count())

    def test_manage_url(self):
        """Test manage url"""
        self.assertEqual(
            '/drive/web-api/storage-providers/123',
            self._get_manage_url(123)
        )

    def test_manage_methods(self):
        """Test manage methods"""
        manage_url = self._get_manage_url(123)
        response = self.client.get(manage_url)
        self.assertEqual(http.HTTPStatus.UNAUTHORIZED, response.status_code)
        response = self.client.post(manage_url)
        self.assertEqual(http.HTTPStatus.UNAUTHORIZED, response.status_code)
        response = self.client.put(manage_url)
        self.assertEqual(http.HTTPStatus.UNAUTHORIZED, response.status_code)
        response = self.client.delete(manage_url)
        self.assertEqual(http.HTTPStatus.UNAUTHORIZED, response.status_code)

        self.client.force_login(User.objects.create_user('lalala'))
        response = self.client.get(manage_url)
        self.assertEqual(http.HTTPStatus.NOT_FOUND, response.status_code)
        response = self.client.put(manage_url)
        self.assertEqual(http.HTTPStatus.METHOD_NOT_ALLOWED, response.status_code)
        response = self.client.post(manage_url)
        self.assertEqual(http.HTTPStatus.NOT_FOUND, response.status_code)
        response = self.client.delete(manage_url)
        self.assertEqual(http.HTTPStatus.NOT_FOUND, response.status_code)

    def test_manage_as_admin(self):
        """Test manage as admin"""
        admin_user = User.objects.create_superuser('gg')
        normal_user = User.objects.create_user('deathprophet')
        sp_a, root_folder_a = create_storage_provider_helper(
            'sp_a', StorageProviderTypeEnum.LOCAL_PATH.value,
            '/var',
        )
        sp_b, root_folder_b = create_storage_provider_helper(
            'sp_b', StorageProviderTypeEnum.LOCAL_PATH.value,
            '/bin',
        )
        StorageProviderUser.objects.create(
            storage_provider=sp_b,
            user=normal_user,
            permission=StorageProviderUser.PERMISSION.READ,
        )
        sp_a_data = dict(
            id=sp_a.pk,
            name=sp_a.name,
            type=sp_a.type,
            path=sp_a.path,
            rootFolder=str(root_folder_a.pk),
            indexing=sp_a.indexing,
            usedSpace=0,
            totalSpace=0,
            permissions=[],
        )
        sp_b_data = dict(
            id=sp_b.pk,
            name=sp_b.name,
            type=sp_b.type,
            path=sp_b.path,
            rootFolder=str(root_folder_b.pk),
            indexing=sp_b.indexing,
            usedSpace=0,
            totalSpace=0,
            permissions=[],
        )
        sp_b_data_p = sp_b_data.copy()
        sp_b_data_p['permissions'] = [
            dict(
                permission=StorageProviderUser.PERMISSION.READ,
                user=dict(
                    id=normal_user.pk,
                    username=normal_user.username,
                )
            )
        ]

        self.client.force_login(admin_user)
        # Test get sp_a
        response = self.client.get(self._get_manage_url(sp_a.pk))
        self.assertEqual(http.HTTPStatus.OK, response.status_code)
        self.assertEqual(sp_a_data, response.json())

        # Test get sp_b
        response = self.client.get(self._get_manage_url(sp_b.pk))
        self.assertEqual(http.HTTPStatus.OK, response.status_code)
        self.assertEqual(sp_b_data_p, response.json())

        # Test update sp_a path
        sp_a.indexing = False
        sp_a.save()
        response = self.client.post(
            self._get_manage_url(sp_a.pk),
            dict(
                name=sp_a.name,
                type=sp_a.type,
                path='/var/lib',
            ),
            content_type=MIMETYPE_JSON,
            QUERY_STRING='action=basic',
        )
        self.assertEqual(http.HTTPStatus.OK, response.status_code)
        received_data = response.json()
        del received_data['usedSpace']
        del received_data['totalSpace']
        self.assertEqual(dict(
            id=sp_a_data['id'],
            name=sp_a_data['name'],
            type=sp_a_data['type'],
            path='/var/lib',
            rootFolder=sp_a_data['rootFolder'],
            indexing=True,
            permissions=[],
        ), received_data)
        sp_a.refresh_from_db()
        self.assertEqual(sp_a_data['name'], sp_a.name)
        self.assertEqual(sp_a_data['type'], sp_a.type)
        self.assertEqual('/var/lib', sp_a.path)
        self.assertTrue(sp_a.indexing)

        # Test update sp_a permission
        response = self.client.post(
            self._get_manage_url(sp_a.pk),
            dict(
                permissions=[
                    dict(
                        permission=StorageProviderUser.PERMISSION.READ_WRITE,
                        user=dict(
                            id=normal_user.pk,
                        ),
                    ),
                ],
            ),
            content_type=MIMETYPE_JSON,
            QUERY_STRING='action=permissions',
        )
        self.assertEqual(http.HTTPStatus.OK, response.status_code)
        received_data = response.json()
        del received_data['usedSpace']
        del received_data['totalSpace']
        self.assertEqual(dict(
            id=sp_a.pk,
            name=sp_a_data['name'],
            type=sp_a_data['type'],
            path='/var/lib',
            rootFolder=sp_a_data['rootFolder'],
            indexing=True,
            permissions=[
                dict(
                    permission=StorageProviderUser.PERMISSION.READ_WRITE,
                    user=dict(
                        id=normal_user.pk,
                        username=normal_user.username,
                    )
                )
            ],
        ), received_data)
        self.assertEqual(
            1,
            StorageProviderUser.objects.filter(
                storage_provider=sp_a,
            ).count()
        )
        self.assertEqual(
            StorageProviderUser.PERMISSION.READ_WRITE,
            StorageProviderUser.objects.filter(
                storage_provider=sp_a,
                user=normal_user,
            ).first().permission
        )

        # Delete
        response = self.client.delete(self._get_manage_url(sp_a.pk))
        self.assertEqual(http.HTTPStatus.OK, response.status_code)
        self.assertEqual({}, response.json())
        self.assertFalse(StorageProvider.objects.filter(pk=sp_a.pk).exists())
        self.assertTrue(StorageProvider.objects.filter(pk=sp_b.pk).exists())
        response = self.client.get(self._get_manage_url(sp_a.pk))
        self.assertEqual(http.HTTPStatus.NOT_FOUND, response.status_code)


    def test_manage_as_normal_user(self):
        """Test manage as normal user"""
        normal_user = User.objects.create_user('deathprophet')
        sp_a, _ = create_storage_provider_helper(
            'sp_a', StorageProviderTypeEnum.LOCAL_PATH.value,
            '/var',
        )
        sp_b, root_folder_b = create_storage_provider_helper(
            'sp_b', StorageProviderTypeEnum.LOCAL_PATH.value,
            '/bin',
        )
        sp_c, root_folder_c = create_storage_provider_helper(
            'sp_c', StorageProviderTypeEnum.LOCAL_PATH.value,
            '/etc',
        )
        StorageProviderUser.objects.create(
            storage_provider=sp_b,
            user=normal_user,
            permission=StorageProviderUser.PERMISSION.READ,
        )
        StorageProviderUser.objects.create(
            storage_provider=sp_c,
            user=normal_user,
            permission=StorageProviderUser.PERMISSION.ADMIN,
        )
        sp_b_data = dict(
            id=sp_b.pk,
            name=sp_b.name,
            type=sp_b.type,
            path=sp_b.path,
            rootFolder=str(root_folder_b.pk),
            indexing=sp_b.indexing,
            usedSpace=0,
            totalSpace=0,
            permissions=[],
        )
        sp_b_data_p = sp_b_data.copy()
        sp_b_data_p['permissions'] = [
            dict(
                permission=StorageProviderUser.PERMISSION.READ,
                user=dict(
                    id=normal_user.pk,
                    username=normal_user.username,
                )
            )
        ]
        sp_c_data = dict(
            id=sp_c.pk,
            name=sp_c.name,
            type=sp_c.type,
            path=sp_c.path,
            rootFolder=str(root_folder_c.pk),
            indexing=sp_c.indexing,
            usedSpace=0,
            totalSpace=0,
            permissions=[],
        )
        sp_c_data_p = sp_c_data.copy()
        sp_c_data_p['permissions'] = [
            dict(
                permission=StorageProviderUser.PERMISSION.ADMIN,
                user=dict(
                    id=normal_user.pk,
                    username=normal_user.username,
                )
            )
        ]

        self.client.force_login(normal_user)
        # Test get sp_a
        response = self.client.get(self._get_manage_url(sp_a.pk))
        self.assertEqual(http.HTTPStatus.FORBIDDEN, response.status_code)
        self.assertEqual(
            dict(error='No permission to perform the operation.'),
            response.json()
        )
        # Test get sp_b
        response = self.client.get(
            self._get_manage_url(sp_b.pk),
            dict(permissions='false'),
        )
        self.assertEqual(http.HTTPStatus.OK, response.status_code)
        self.assertEqual(sp_b_data, response.json())
        # Test get sp_b with permission
        response = self.client.get(
            self._get_manage_url(sp_b.pk),
            dict(permissions='true'),
        )
        self.assertEqual(http.HTTPStatus.FORBIDDEN, response.status_code)
        self.assertEqual(
            dict(error='No permission to access the resource.'),
            response.json()
        )
        # Test get sp_c
        response = self.client.get(self._get_manage_url(sp_c.pk))
        self.assertEqual(http.HTTPStatus.OK, response.status_code)
        self.assertEqual(sp_c_data_p, response.json())

        # Test post invalid action
        response = self.client.post(
            self._get_manage_url(sp_c.pk),
            {},
            content_type=MIMETYPE_JSON,
            QUERY_STRING='action=i-duno-lol',
        )
        self.assertEqual(http.HTTPStatus.BAD_REQUEST, response.status_code)
        self.assertEqual(dict(error='Invalid action!'), response.json())

        # Test post invalid permission
        response = self.client.post(
            self._get_manage_url(sp_c.pk),
            dict(
                permissions=[
                    dict(
                        permission=123456,
                        user=dict(
                            id=normal_user.pk,
                        ),
                    ),
                ],
            ),
            content_type=MIMETYPE_JSON,
            QUERY_STRING='action=permissions',
        )
        self.assertEqual(http.HTTPStatus.BAD_REQUEST, response.status_code)
        self.assertEqual(dict(error='Invalid permission type!'), response.json())

        # Test post invalid user id
        response = self.client.post(
            self._get_manage_url(sp_c.pk),
            dict(
                permissions=[
                    dict(
                        permission=StorageProviderUser.PERMISSION.READ_WRITE,
                        user=dict(
                            id=normal_user.pk+100,
                        ),
                    ),
                ],
            ),
            content_type=MIMETYPE_JSON,
            QUERY_STRING='action=permissions',
        )
        self.assertEqual(http.HTTPStatus.BAD_REQUEST, response.status_code)
        self.assertEqual(dict(error='User not found!'), response.json())

        # Delete
        response = self.client.delete(self._get_manage_url(sp_c.pk))
        self.assertEqual(http.HTTPStatus.OK, response.status_code)
        self.assertEqual({}, response.json())
        self.assertFalse(StorageProvider.objects.filter(pk=sp_c.pk).exists())
        self.assertTrue(StorageProvider.objects.filter(pk=sp_a.pk).exists())
        self.assertTrue(StorageProvider.objects.filter(pk=sp_b.pk).exists())
        response = self.client.get(self._get_manage_url(sp_c.pk))
        self.assertEqual(http.HTTPStatus.NOT_FOUND, response.status_code)
