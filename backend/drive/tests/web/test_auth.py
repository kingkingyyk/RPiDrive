import http

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .shared import MIMETYPE_JSON

class TestAuth(TestCase):
    """Test auth views"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='hello'
        )
        self.is_logged_in_url = reverse('user.is_logged_in')
        self.login_url = reverse('user.login')
        self.logout_url = reverse('user.logout')

    def tearDown(self):
        self.user.delete()

    def test_is_logged_in_url(self):
        """Test is_logged_in url value"""
        self.assertEqual('/drive/web-api/auth/logged-in', self.is_logged_in_url)

    def test_is_logged_in_methods(self):
        """Test is logged in methods"""
        response = self.client.post(self.is_logged_in_url)
        self.assertEqual(http.HTTPStatus.METHOD_NOT_ALLOWED, response.status_code)

        response = self.client.put(self.is_logged_in_url)
        self.assertEqual(http.HTTPStatus.METHOD_NOT_ALLOWED, response.status_code)

        response = self.client.delete(self.is_logged_in_url)
        self.assertEqual(http.HTTPStatus.METHOD_NOT_ALLOWED, response.status_code)

    def test_is_logged_in(self):
        """Test is logged in"""
        response = self.client.get(self.is_logged_in_url)
        self.assertEqual(http.HTTPStatus.FORBIDDEN, response.status_code)
        self.assertEqual(dict(result=False), response.json())

        self.client.force_login(self.user)
        response = self.client.get(self.is_logged_in_url)
        self.assertEqual(http.HTTPStatus.OK, response.status_code)
        self.assertEqual(dict(result=True), response.json())

    def test_user_login_url(self):
        """Test user_login url value"""
        self.assertEqual('/drive/web-api/auth/login', self.login_url)

    def test_user_login_methods(self):
        """Test user_login methods"""
        response = self.client.get(self.login_url)
        self.assertEqual(http.HTTPStatus.METHOD_NOT_ALLOWED, response.status_code)

        response = self.client.put(self.login_url)
        self.assertEqual(http.HTTPStatus.METHOD_NOT_ALLOWED, response.status_code)

        response = self.client.delete(self.login_url)
        self.assertEqual(http.HTTPStatus.METHOD_NOT_ALLOWED, response.status_code)

    def test_user_login(self):
        """Test user_login"""
        # Wrong password
        response = self.client.post(
            self.login_url,
            dict(
                username=self.user.username,
                password='iduno'
            ),
            content_type=MIMETYPE_JSON,
        )
        self.assertEqual(http.HTTPStatus.UNAUTHORIZED, response.status_code)
        self.assertEqual(
            dict(error='Invalid username/password'),
            response.json()
        )

        self.user.set_password('heh')
        self.user.save()

        # Wrong username
        response = self.client.post(
            self.login_url,
            dict(
                username='nah',
                password='heh'
            ),
            content_type=MIMETYPE_JSON,
        )
        self.assertEqual(http.HTTPStatus.UNAUTHORIZED, response.status_code)
        self.assertEqual(
            dict(error='Invalid username/password'),
            response.json()
        )

        # Correct
        response = self.client.post(
            self.login_url,
            dict(
                username=self.user.username,
                password='heh'
            ),
            content_type=MIMETYPE_JSON,
        )
        self.assertEqual(http.HTTPStatus.OK, response.status_code)
        self.assertEqual({}, response.json())

        # Check is logged in is working
        response = self.client.get(self.is_logged_in_url)
        self.assertEqual(http.HTTPStatus.OK, response.status_code)
        self.assertEqual(dict(result=True), response.json())

    def test_user_logout_url(self):
        """Test user_logout url value"""
        self.assertEqual('/drive/web-api/auth/logout', self.logout_url)

    def test_user_logout_methods(self):
        """Test user_logout methods"""
        # Not logged in
        response = self.client.get(self.logout_url)
        self.assertEqual(http.HTTPStatus.UNAUTHORIZED, response.status_code)

        response = self.client.put(self.logout_url)
        self.assertEqual(http.HTTPStatus.UNAUTHORIZED, response.status_code)

        response = self.client.delete(self.logout_url)
        self.assertEqual(http.HTTPStatus.UNAUTHORIZED, response.status_code)

        # Logged in
        self.client.force_login(self.user)
        response = self.client.get(self.logout_url)
        self.assertEqual(http.HTTPStatus.METHOD_NOT_ALLOWED, response.status_code)

        response = self.client.put(self.logout_url)
        self.assertEqual(http.HTTPStatus.METHOD_NOT_ALLOWED, response.status_code)

        response = self.client.delete(self.logout_url)
        self.assertEqual(http.HTTPStatus.METHOD_NOT_ALLOWED, response.status_code)

    def test_user_logout(self):
        """Test user_logout"""
        # Logout without login
        response = self.client.post(self.logout_url)
        self.assertEqual(http.HTTPStatus.UNAUTHORIZED, response.status_code) # Redirect

        password = 'heh'
        self.user.set_password(password)
        self.user.save()

        # Login
        response = self.client.post(
            self.login_url,
            dict(
                username=self.user.username,
                password='heh'
            ),
            content_type=MIMETYPE_JSON,
        )
        self.assertEqual(http.HTTPStatus.OK, response.status_code)
        self.assertNotEqual(
            'Thu, 01 Jan 1970 00:00:00 GMT',
            self.client.cookies['sessionid']['expires']
        )

        # Logout
        response = self.client.post(self.logout_url)
        self.assertEqual(http.HTTPStatus.OK, response.status_code)
        self.assertEqual(
            'Thu, 01 Jan 1970 00:00:00 GMT',
            self.client.cookies['sessionid']['expires']
        )

        # Logout again
        response = self.client.post(self.logout_url)
        self.assertEqual(http.HTTPStatus.UNAUTHORIZED, response.status_code) # Redirect

        # Check if logged in
        response = self.client.get(self.is_logged_in_url)
        self.assertEqual(http.HTTPStatus.FORBIDDEN, response.status_code)
