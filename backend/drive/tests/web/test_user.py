import http

from typing import Dict

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from drive.cache import ModelCache
from drive.tests.web.shared import MIMETYPE_JSON
from drive.views.web.shared import format_dt_iso

class TestUser(TestCase):
    """Test user views"""

    def setUp(self):
        self.get_users_url = reverse('user.list')
        self.create_user_url = reverse('user.create')
        self.get_current_user_url = reverse('user.get')
        self.manage_user_url = self._get_manage_user_url(123)

        self.admin_user = User.objects.create(
            username='adminz',
            first_name='anya',
            last_name='forger',
            email='nope',
            is_superuser=True,
            is_staff=True,
        )
        self.normal_user = User.objects.create(
            username='noob',
            first_name='pika',
            last_name='chu',
            email='abc@abc.com'
        )
        ModelCache.disable()

    def tearDown(self):
        User.objects.all().delete()
        ModelCache.enable()

    def _get_manage_user_url(self, i_d: int) -> str:
        return reverse('user.manage', args=[i_d])

    def _serialize_user(self, user: User) -> Dict:
        return dict(
            id=user.pk,
            username=user.username,
            firstName=user.first_name,
            lastName=user.last_name,
            email=user.email,
            isActive=user.is_active,
            isSuperuser=user.is_superuser,
            lastLogin=format_dt_iso(user.last_login),
        )

    def test_get_users_url(self):
        """Test get_users url"""
        self.assertEqual(
            '/drive/web-api/users',
            self.get_users_url
        )

    def test_get_users_methods(self):
        """Test get_users http methods"""
        # Not logged in
        response = self.client.get(self.get_users_url)
        self.assertEqual(http.HTTPStatus.UNAUTHORIZED, response.status_code)

        response = self.client.post(self.get_users_url)
        self.assertEqual(http.HTTPStatus.UNAUTHORIZED, response.status_code)

        response = self.client.put(self.get_users_url)
        self.assertEqual(http.HTTPStatus.UNAUTHORIZED, response.status_code)

        response = self.client.delete(self.get_users_url)
        self.assertEqual(http.HTTPStatus.UNAUTHORIZED, response.status_code)

        # Logged in as admin
        self.client.force_login(self.admin_user)
        response = self.client.post(self.get_users_url)
        self.assertEqual(http.HTTPStatus.METHOD_NOT_ALLOWED, response.status_code)

        response = self.client.put(self.get_users_url)
        self.assertEqual(http.HTTPStatus.METHOD_NOT_ALLOWED, response.status_code)

        response = self.client.delete(self.get_users_url)
        self.assertEqual(http.HTTPStatus.METHOD_NOT_ALLOWED, response.status_code)

        # Logged in as normal user
        self.client.force_login(self.normal_user)
        response = self.client.get(self.get_users_url)
        self.assertEqual(http.HTTPStatus.UNAUTHORIZED, response.status_code)

        response = self.client.post(self.get_users_url)
        self.assertEqual(http.HTTPStatus.UNAUTHORIZED, response.status_code)

        response = self.client.put(self.get_users_url)
        self.assertEqual(http.HTTPStatus.UNAUTHORIZED, response.status_code)

        response = self.client.delete(self.get_users_url)
        self.assertEqual(http.HTTPStatus.UNAUTHORIZED, response.status_code)

    def test_get_users(self):
        """Test get_users"""
        # Not logged in
        response = self.client.get(self.get_users_url)
        self.assertEqual(http.HTTPStatus.UNAUTHORIZED, response.status_code)

        # Logged in as normal user
        self.client.force_login(self.normal_user)
        response = self.client.get(self.get_users_url)
        self.assertEqual(http.HTTPStatus.UNAUTHORIZED, response.status_code)

        # Logged in as admin
        self.client.force_login(self.admin_user)
        response = self.client.get(self.get_users_url)
        self.assertEqual(http.HTTPStatus.OK, response.status_code)
        expected_data = dict(
            values=[
                self._serialize_user(self.admin_user),
                self._serialize_user(self.normal_user),
            ]
        )
        self.assertEqual(expected_data, response.json())

    def test_create_user_url(self):
        """Test create_user url"""
        self.assertEqual(
            '/drive/web-api/users/create',
            self.create_user_url
        )

    def test_create_user_methods(self):
        """Test create_user method"""
        # Not logged in
        response = self.client.get(self.create_user_url)
        self.assertEqual(http.HTTPStatus.UNAUTHORIZED, response.status_code)

        response = self.client.post(self.create_user_url)
        self.assertEqual(http.HTTPStatus.UNAUTHORIZED, response.status_code)

        response = self.client.put(self.create_user_url)
        self.assertEqual(http.HTTPStatus.UNAUTHORIZED, response.status_code)

        response = self.client.delete(self.create_user_url)
        self.assertEqual(http.HTTPStatus.UNAUTHORIZED, response.status_code)

        # Logged in as admin
        self.client.force_login(self.admin_user)
        response = self.client.get(self.create_user_url)
        self.assertEqual(http.HTTPStatus.METHOD_NOT_ALLOWED, response.status_code)

        response = self.client.put(self.create_user_url)
        self.assertEqual(http.HTTPStatus.METHOD_NOT_ALLOWED, response.status_code)

        response = self.client.delete(self.create_user_url)
        self.assertEqual(http.HTTPStatus.METHOD_NOT_ALLOWED, response.status_code)

        # Logged in as normal user
        self.client.force_login(self.normal_user)
        response = self.client.get(self.create_user_url)
        self.assertEqual(http.HTTPStatus.UNAUTHORIZED, response.status_code)

        response = self.client.post(self.create_user_url)
        self.assertEqual(http.HTTPStatus.UNAUTHORIZED, response.status_code)

        response = self.client.put(self.create_user_url)
        self.assertEqual(http.HTTPStatus.UNAUTHORIZED, response.status_code)

        response = self.client.delete(self.create_user_url)
        self.assertEqual(http.HTTPStatus.UNAUTHORIZED, response.status_code)

    def test_create_user(self):
        """Test create_user"""
        self.client.force_login(self.admin_user)

        # Post no data
        response = self.client.post(self.create_user_url)
        self.assertEqual(http.HTTPStatus.BAD_REQUEST, response.status_code)
        self.assertEqual(dict(error='No data received.'), response.json())

        # Post invalid data
        response = self.client.post(
            self.create_user_url,
            data={},
            content_type=MIMETYPE_JSON,
        )
        self.assertEqual(http.HTTPStatus.BAD_REQUEST, response.status_code)
        self.assertEqual(dict(error='Invalid data received.'), response.json())

        # Post valid data
        post_data = dict(
            username='nope',
            password='some very secure password',
            firstName='nvidia',
            lastName='amd',
            email='jensen@lisa.com',
            isActive=True,
            isSuperuser=True,
        )
        response = self.client.post(
            self.create_user_url,
            data=post_data,
            content_type=MIMETYPE_JSON,
        )
        self.assertEqual(http.HTTPStatus.CREATED, response.status_code)
        data = response.json()
        self.assertGreater(data['id'], 0)
        del data['id']
        del data['lastLogin']
        for key, value in post_data.items():
            if key == 'password':
                continue
            self.assertEqual(value, data[key])

        # Same user name
        response = self.client.post(
            self.create_user_url,
            data=post_data,
            content_type=MIMETYPE_JSON,
        )
        self.assertEqual(http.HTTPStatus.BAD_REQUEST, response.status_code)
        self.assertEqual(dict(error='Username already exists.'), response.json())

    def test_get_current_user_url(self):
        """Test get_users url"""
        self.assertEqual(
            '/drive/web-api/users/current',
            self.get_current_user_url
        )

    def test_get_current_user_methods(self):
        """Test get_users methods"""
        # Not logged in
        response = self.client.get(self.get_current_user_url)
        self.assertEqual(http.HTTPStatus.UNAUTHORIZED, response.status_code)

        response = self.client.post(self.get_current_user_url)
        self.assertEqual(http.HTTPStatus.UNAUTHORIZED, response.status_code)

        response = self.client.put(self.get_current_user_url)
        self.assertEqual(http.HTTPStatus.UNAUTHORIZED, response.status_code)

        response = self.client.delete(self.get_current_user_url)
        self.assertEqual(http.HTTPStatus.UNAUTHORIZED, response.status_code)

        # Logged in
        self.client.force_login(self.normal_user)
        response = self.client.post(self.get_current_user_url)
        self.assertEqual(http.HTTPStatus.METHOD_NOT_ALLOWED, response.status_code)

        response = self.client.put(self.get_current_user_url)
        self.assertEqual(http.HTTPStatus.METHOD_NOT_ALLOWED, response.status_code)

        response = self.client.delete(self.get_current_user_url)
        self.assertEqual(http.HTTPStatus.METHOD_NOT_ALLOWED, response.status_code)

    def test_get_current_user(self):
        """Test get_current_user"""
        self.client.force_login(self.admin_user)
        response = self.client.get(self.get_current_user_url)
        self.assertEqual(http.HTTPStatus.OK, response.status_code)
        self.assertEqual(
            self._serialize_user(self.admin_user),
            response.json()
        )

        self.client.force_login(self.normal_user)
        response = self.client.get(self.get_current_user_url)
        self.assertEqual(http.HTTPStatus.OK, response.status_code)
        self.assertEqual(
            self._serialize_user(self.normal_user),
            response.json()
        )

    def test_manage_user_url(self):
        """Test manage_user url"""
        self.assertEqual(
            '/drive/web-api/users/123',
            self.manage_user_url
        )

    def test_manage_user_methods(self):
        """Test manage_user method"""
        # Not logged in
        response = self.client.get(self.manage_user_url)
        self.assertEqual(http.HTTPStatus.UNAUTHORIZED, response.status_code)

        response = self.client.post(self.manage_user_url)
        self.assertEqual(http.HTTPStatus.UNAUTHORIZED, response.status_code)

        response = self.client.put(self.manage_user_url)
        self.assertEqual(http.HTTPStatus.UNAUTHORIZED, response.status_code)

        response = self.client.delete(self.manage_user_url)
        self.assertEqual(http.HTTPStatus.UNAUTHORIZED, response.status_code)

        # Logged in as admin
        self.client.force_login(self.admin_user)
        response = self.client.put(self.manage_user_url)
        self.assertEqual(http.HTTPStatus.METHOD_NOT_ALLOWED, response.status_code)

        # Logged in as normal user
        self.client.force_login(self.normal_user)
        response = self.client.get(self.manage_user_url)
        self.assertEqual(http.HTTPStatus.UNAUTHORIZED, response.status_code)

        response = self.client.post(self.manage_user_url)
        self.assertEqual(http.HTTPStatus.UNAUTHORIZED, response.status_code)

        response = self.client.put(self.manage_user_url)
        self.assertEqual(http.HTTPStatus.UNAUTHORIZED, response.status_code)

        response = self.client.delete(self.manage_user_url)
        self.assertEqual(http.HTTPStatus.UNAUTHORIZED, response.status_code)

    def test_manage_user(self):
        """Test manage_user"""
        self.client.force_login(self.admin_user)

        # User not found
        response = self.client.get(self.manage_user_url)
        self.assertEqual(http.HTTPStatus.NOT_FOUND, response.status_code)
        self.assertEqual(dict(error='User not found.'), response.json())

        # User found
        response = self.client.get(self._get_manage_user_url(self.normal_user.pk))
        self.assertEqual(http.HTTPStatus.OK, response.status_code)
        self.assertEqual(self._serialize_user(self.normal_user), response.json())

        # Delete user
        temp_user = User.objects.create(
            username='viper',
            first_name='venomancer',
            last_name='chaos',
            email='knight@slark.com'
        )
        response = self.client.delete(self._get_manage_user_url(temp_user.pk))
        self.assertEqual(http.HTTPStatus.OK, response.status_code)
        self.assertEqual({}, response.json())
        # Make sure user no longer exists
        self.assertFalse(User.objects.filter(username='viper').exists())
        response = self.client.get(self._get_manage_user_url(temp_user.pk))
        self.assertEqual(http.HTTPStatus.NOT_FOUND, response.status_code)
        self.assertEqual(dict(error='User not found.'), response.json())

        # Update user fields
        temp_user = User.objects.create(
            username='viper',
            first_name='venomancer',
            last_name='chaos',
            email='knight@slark.com',
        )
        temp_user.set_password('abcdef')
        temp_user.save()
        post_data = dict(
            username='sven',
            password=None,
            firstName='lala',
            lastName='messi',
            email='lol@lel.com',
            isActive=False,
            isSuperuser=True,
        )
        response = self.client.post(
            self._get_manage_user_url(temp_user.pk),
            data=post_data,
            content_type=MIMETYPE_JSON,
        )
        self.assertEqual(http.HTTPStatus.OK, response.status_code)
        data = response.json()
        self.assertEqual(temp_user.pk, data['id'])
        for key, value in post_data.items():
            if key == 'password':
                continue
            self.assertEqual(value, data[key])
        temp_user.refresh_from_db()
        self.assertTrue(temp_user.check_password('abcdef'))

        # Update password
        post_data['password'] = 'lollipop'
        response = self.client.post(
            self._get_manage_user_url(temp_user.pk),
            data=post_data,
            content_type=MIMETYPE_JSON,
        )
        self.assertEqual(http.HTTPStatus.OK, response.status_code)
        temp_user.refresh_from_db()
        self.assertTrue(temp_user.check_password(post_data['password']))
