import http
import os

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from drive.models import (
    StorageProvider,
    StorageProviderTypeEnum,
    System,
)
from drive.tests.web.shared import MIMETYPE_JSON

class TestSystem(TestCase):
    """Test system views"""

    def setUp(self):
        self.initialize_system_url = reverse('system.initialize')
        self.get_network_info_url = reverse('system.network_usage')
        self.get_system_info_url = reverse('system.info')

        self.admin_user = User.objects.create_superuser('admin')
        self.normal_user = User.objects.create_user('noob')

    def tearDown(self):
        StorageProvider.objects.all().delete()
        System.objects.all().delete()
        User.objects.all().delete()

    def _test_info_url(self, url: str):
        # Not logged in
        response = self.client.get(url)
        self.assertEqual(http.HTTPStatus.UNAUTHORIZED, response.status_code)

        response = self.client.post(url)
        self.assertEqual(http.HTTPStatus.UNAUTHORIZED, response.status_code)

        response = self.client.put(url)
        self.assertEqual(http.HTTPStatus.UNAUTHORIZED, response.status_code)

        response = self.client.delete(url)
        self.assertEqual(http.HTTPStatus.UNAUTHORIZED, response.status_code)

        # Logged in as admin
        self.client.force_login(self.admin_user)
        response = self.client.post(url)
        self.assertEqual(http.HTTPStatus.METHOD_NOT_ALLOWED, response.status_code)

        response = self.client.put(url)
        self.assertEqual(http.HTTPStatus.METHOD_NOT_ALLOWED, response.status_code)

        response = self.client.delete(url)
        self.assertEqual(http.HTTPStatus.METHOD_NOT_ALLOWED, response.status_code)

        # Logged in as normal user
        self.client.force_login(self.normal_user)
        response = self.client.get(url)
        self.assertEqual(http.HTTPStatus.UNAUTHORIZED, response.status_code)

        response = self.client.post(url)
        self.assertEqual(http.HTTPStatus.UNAUTHORIZED, response.status_code)

        response = self.client.put(url)
        self.assertEqual(http.HTTPStatus.UNAUTHORIZED, response.status_code)

        response = self.client.delete(url)
        self.assertEqual(http.HTTPStatus.UNAUTHORIZED, response.status_code)


    def test_initialize_system_url(self):
        """Test initialize system url"""
        self.assertEqual(
            '/drive/web-api/system/initialize',
            self.initialize_system_url
        )

    def test_initialize_system_methods(self):
        """Test initialize system methods"""
        response = self.client.put(self.initialize_system_url)
        self.assertEqual(http.HTTPStatus.METHOD_NOT_ALLOWED, response.status_code)

        response = self.client.delete(self.initialize_system_url)
        self.assertEqual(http.HTTPStatus.METHOD_NOT_ALLOWED, response.status_code)

    def test_initialize_system(self): # pylint: disable=too-many-statements
        """Test initialize system"""
        self.assertEqual(0, System.objects.count())
        User.objects.all().delete()

        # First init
        response = self.client.get(self.initialize_system_url)
        self.assertEqual(http.HTTPStatus.OK, response.status_code)
        self.assertEqual({}, response.json())
        self.assertEqual(1, System.objects.count())
        system = System.objects.first()

        # Perform invalid init
        data = dict(
            initKey='abc i duno hehehe',
            storageProvider=dict(
                name='my drive',
                type=StorageProviderTypeEnum.LOCAL_PATH,
                path=os.getcwd(),
            ),
            user=dict(
                username='anya-forger',
                password='i love peanut',
                firstName='anya',
                lastName='forger',
                email='anyaforger@mail.com'
            )
        )
        response = self.client.post(
            self.initialize_system_url,
            data,
            content_type=MIMETYPE_JSON,
        )
        self.assertEqual(http.HTTPStatus.UNAUTHORIZED, response.status_code)
        self.assertEqual(
            dict(error='Invalid initialization key! Please check server console.'),
            response.json()
        )
        self.assertEqual(0, StorageProvider.objects.count())
        self.assertEqual(0, User.objects.count())
        data['initKey'] = system.init_key

        # Correct key but incorrect storage provider
        data['storageProvider']['path'] = '/abcdef'
        response = self.client.post(
            self.initialize_system_url,
            data,
            content_type=MIMETYPE_JSON,
        )
        self.assertEqual(http.HTTPStatus.INTERNAL_SERVER_ERROR, response.status_code)
        self.assertEqual(
            dict(error='Exception: Path /abcdef doesn\'t exist!'),
            response.json()
        )
        self.assertEqual(0, StorageProvider.objects.count())
        self.assertEqual(0, User.objects.count())
        data['storageProvider']['path'] = os.getcwd()

        # Correct key but incorrect password
        data['user']['password'] = ''
        response = self.client.post(
            self.initialize_system_url,
            data,
            content_type=MIMETYPE_JSON,
        )
        self.assertEqual(http.HTTPStatus.BAD_REQUEST, response.status_code)
        self.assertTrue('user -> password' in response.json()['error'])
        self.assertEqual(0, StorageProvider.objects.count())
        self.assertEqual(0, User.objects.count())
        data['user']['password'] = 'i love peanut'

        # Perform init
        response = self.client.post(
            self.initialize_system_url,
            data,
            content_type=MIMETYPE_JSON,
        )
        self.assertEqual(http.HTTPStatus.OK, response.status_code)
        self.assertEqual({}, response.json())
        self.assertTrue(System.objects.first().initialized)
        self.assertEqual(1, StorageProvider.objects.count())
        self.assertEqual(1, User.objects.count())
        s_p = StorageProvider.objects.first()
        self.assertEqual(data['storageProvider']['name'], s_p.name)
        self.assertEqual(data['storageProvider']['type'], s_p.type)
        self.assertEqual(data['storageProvider']['path'], s_p.path)
        self.assertTrue(s_p.indexing)
        user = User.objects.first()
        self.assertEqual(data['user']['username'], user.username)
        self.assertTrue(user.check_password(data['user']['password']))
        self.assertEqual(data['user']['firstName'], user.first_name)
        self.assertEqual(data['user']['lastName'], user.last_name)
        self.assertEqual(data['user']['email'], user.email)

        # Redo init
        response = self.client.post(
            self.initialize_system_url,
            data,
            content_type=MIMETYPE_JSON,
        )
        self.assertEqual(http.HTTPStatus.BAD_REQUEST, response.status_code)
        self.assertEqual(
            dict(error='System has already been initialized!'),
            response.json()
        )
        self.assertTrue(System.objects.first().initialized)
        self.assertEqual(1, StorageProvider.objects.count())
        self.assertEqual(1, User.objects.count())

        # Get init status
        response = self.client.get(self.initialize_system_url)
        self.assertEqual(http.HTTPStatus.UNAUTHORIZED, response.status_code)
        self.assertEqual(dict(error=''), response.json())

    def test_get_network_info_url(self):
        """Test network info url"""
        self.assertEqual(
            '/drive/web-api/system/network-usage',
            self.get_network_info_url,
        )

    def test_get_network_info_methods(self):
        """Test network info methods"""
        self._test_info_url(self.get_network_info_url)

    def test_get_network_info(self):
        """Test get_network_info"""
        self.client.force_login(self.admin_user)
        response = self.client.get(self.get_network_info_url)
        self.assertEqual(http.HTTPStatus.OK, response.status_code)
        keys = {'downloadSpeed', 'uploadSpeed', 'downloadTotal', 'uploadTotal'}
        self.assertEqual(keys, response.json().keys())

    def test_get_system_info_url(self):
        """Test system info url"""
        self.assertEqual(
            '/drive/web-api/system/info',
            self.get_system_info_url,
        )

    def test_get_system_info_methods(self):
        """Test system info methods"""
        self._test_info_url(self.get_system_info_url)

    def test_get_system_info(self):
        """Test system info"""
        self.client.force_login(self.admin_user)
        response = self.client.get(self.get_system_info_url)
        self.assertEqual(http.HTTPStatus.OK, response.status_code)
        keys = [
            'cpuCount', 'cpuFrequency', 'cpuUsage',
            'memTotal', 'memUsage', 'disks', 'osName',
            'osArch', 'pythonVersion'
        ]
        for key in keys:
            self.assertTrue(key in response.json())
        disk_keys = [
            'path', 'total', 'used', 'free', 'percent'
        ]
        for disk in response.json()['disks']:
            for key in disk_keys:
                self.assertTrue(key in disk)
