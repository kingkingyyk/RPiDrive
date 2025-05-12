from django.contrib.auth.models import User
from django.test import TestCase

from rpidrive.controllers.exceptions import NoPermissionException
from rpidrive.controllers.user import (
    InvalidUsernameException,
    InvalidPasswordException,
    UserNotFoundException,
    create_user,
    delete_user,
    get_user,
    get_users,
    update_user,
)


class TestUserController(TestCase):
    """Test User controller"""

    def setUp(self):
        self.admin_user = User.objects.create_superuser("hehe")
        self.admin_user_2 = User.objects.create_superuser("anya")
        self.normal_user = User.objects.create_user("noob")

    def tearDown(self):
        User.objects.all().delete()

    def test_create_user_1(self):
        """Test create_user (admin)"""
        new_user = create_user(
            self.admin_user,
            "XD",
            "o@xd.com",
            "hehe",
            True,
            first_name="X",
            last_name="D",
        )
        self.assertEqual(new_user.username, "XD")
        self.assertEqual(new_user.email, "o@xd.com")
        self.assertTrue(new_user.check_password("hehe"))
        self.assertTrue(new_user.is_superuser)
        self.assertEqual(new_user.first_name, "X")
        self.assertEqual(new_user.last_name, "D")

    def test_create_user_2(self):
        """Test create_user (normal)"""
        new_user = create_user(
            self.admin_user,
            "XD",
            "o@xd.com",
            "hehe",
            False,
        )
        self.assertEqual(new_user.username, "XD")
        self.assertEqual(new_user.email, "o@xd.com")
        self.assertTrue(new_user.check_password("hehe"))
        self.assertFalse(new_user.is_superuser)
        self.assertEqual(new_user.first_name, "")
        self.assertEqual(new_user.last_name, "")

    def test_create_user_3(self):
        """Test create_user (No permission)"""
        self.assertRaises(
            NoPermissionException,
            create_user,
            self.normal_user,
            "XD",
            "o@xd.com",
            "hehe",
            False,
        )

    def test_create_user_4(self):
        """Test create_user (Invalid username)"""
        self.assertRaises(
            InvalidUsernameException,
            create_user,
            self.admin_user,
            "",
            "o@xd.com",
            "hehe",
            False,
        )

    def test_create_user_5(self):
        """Test create_user (Invalid password)"""
        self.assertRaises(
            InvalidPasswordException,
            create_user,
            self.admin_user,
            "lelele",
            "o@xd.com",
            "",
            False,
        )

    def test_get_users_1(self):
        """Test get_users (Admin)"""
        self.assertEqual(get_users(self.admin_user).count(), 3)

    def test_get_users_2(self):
        """Test get_users (Normal)"""
        self.assertEqual(get_users(self.normal_user).count(), 3)

    def test_get_user_1(self):
        """Test get_user (self)"""
        self.assertEqual(self.admin_user, get_user(self.admin_user, self.admin_user.pk))
        self.assertEqual(
            self.normal_user, get_user(self.normal_user, self.normal_user.pk)
        )

    def test_get_user_2(self):
        """Test get_user (Admin)"""
        self.assertEqual(self.admin_user, get_user(self.admin_user, self.admin_user.pk))
        self.assertEqual(
            self.normal_user, get_user(self.admin_user, self.normal_user.pk)
        )

    def test_get_user_3(self):
        """Test get_user (Normal)"""
        with self.assertRaises(NoPermissionException):
            get_user(self.normal_user, self.admin_user.pk)

        with self.assertRaises(NoPermissionException):
            get_user(self.normal_user, self.admin_user.pk + 1000)

    def test_get_user_4(self):
        """Test get_user (Invalid id)"""
        with self.assertRaises(UserNotFoundException):
            get_user(self.admin_user, self.admin_user.pk + 1000)

    def test_update_user_1(self):
        """Test update_user (Admin update admin)"""
        update_user(
            self.admin_user,
            self.admin_user_2.pk,
            "ex123@example.com",
            "XDXD444;",
            True,
            is_active=False,
            first_name="sien",
            last_name="pika",
        )
        self.admin_user_2.refresh_from_db()
        self.assertEqual(self.admin_user_2.email, "ex123@example.com")
        self.assertTrue(self.admin_user_2.check_password("XDXD444;"))
        self.assertFalse(self.admin_user_2.is_active)
        self.assertEqual(self.admin_user_2.first_name, "sien")
        self.assertEqual(self.admin_user_2.last_name, "pika")

    def test_update_user_2(self):
        """Test update_user (User update admin)"""
        self.assertRaises(
            NoPermissionException,
            update_user,
            self.normal_user,
            self.admin_user_2.pk,
            "ex123@example.com",
            "XDXD444;",
            True,
            is_active=False,
            first_name="sien",
            last_name="pika",
        )

    def test_update_user_3(self):
        """Test update_user (User update self)"""
        update_user(
            self.normal_user,
            self.normal_user.pk,
            "ex123@example.com",
            "XDXD444;",
            False,
            is_active=True,
            first_name="sien",
            last_name="pika",
        )
        self.normal_user.refresh_from_db()
        self.assertEqual(self.normal_user.email, "ex123@example.com")
        self.assertTrue(self.normal_user.check_password("XDXD444;"))
        self.assertFalse(self.normal_user.is_superuser)
        self.assertTrue(self.normal_user.is_active)
        self.assertEqual(self.normal_user.first_name, "sien")
        self.assertEqual(self.normal_user.last_name, "pika")

    def test_update_user_4(self):
        """Test update_user (User not found)"""
        self.assertRaises(
            UserNotFoundException,
            update_user,
            self.admin_user,
            self.normal_user.pk + 1000,
            "ex123@example.com",
            "XDXD444;",
            True,
        )

    def test_delete_user_1(self):
        """Test delete user (Admin)"""
        delete_user(self.admin_user, self.normal_user.pk)
        self.assertFalse(User.objects.filter(pk=self.normal_user.pk).exists())

    def test_delete_user_2(self):
        """Test delete user (Normal)"""
        self.assertRaises(
            NoPermissionException,
            delete_user,
            self.normal_user,
            self.normal_user.pk,
        )

        self.assertEqual(User.objects.count(), 3)

    def test_delete_user_3(self):
        """Test delete user (User not found)"""
        self.assertRaises(
            UserNotFoundException,
            delete_user,
            self.admin_user,
            self.normal_user.pk + 1000,
        )

        self.assertEqual(User.objects.count(), 3)
