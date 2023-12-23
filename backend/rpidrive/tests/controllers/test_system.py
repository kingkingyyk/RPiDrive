from django.contrib.auth.models import User
from django.test import TestCase

from rpidrive.controllers.exceptions import NoPermissionException
from rpidrive.controllers.system import (
    get_cpu_info,
    get_mem_info,
    get_disk_info,
    get_environ_info,
    get_network_info,
)


class TestSystem(TestCase):
    """Test system controller"""

    def setUp(self):
        self.admin_user = User.objects.create_superuser("a")
        self.normal_user = User.objects.create_user("b")

    def tearDown(self):
        User.objects.all().delete()

    def test_get_cpu_info_1(self):
        """Test get_cpu_info"""
        data = get_cpu_info(self.admin_user).model_dump()
        keys = ["model", "cores", "frequency", "usage"]
        data_type = [str, int, int, float]
        for idx, key in enumerate(keys):
            self.assertTrue(key in data)
            self.assertEqual(data_type[idx], type(data[key]))

    def test_get_cpu_info_2(self):
        """Test get_cpu_info (Normal user)"""
        with self.assertRaises(NoPermissionException):
            get_cpu_info(self.normal_user)

    def test_get_mem_info_1(self):
        """Test get_mem_info"""
        data = get_mem_info(self.admin_user).model_dump()
        keys = ["total", "used", "usage"]
        data_type = [int, int, float]
        for idx, key in enumerate(keys):
            self.assertTrue(key in data)
            self.assertEqual(data_type[idx], type(data[key]))

    def test_get_mem_info_2(self):
        """Test get_mem_info (Normal user)"""
        with self.assertRaises(NoPermissionException):
            get_mem_info(self.normal_user)

    def test_get_disk_info_1(self):
        """Test get disk_info"""
        data = get_disk_info(self.admin_user)[0].model_dump()
        keys = ["name", "total", "used", "free", "percent"]
        data_type = [str, int, int, int, float]
        for idx, key in enumerate(keys):
            self.assertTrue(key in data)
            self.assertEqual(data_type[idx], type(data[key]))

    def test_get_disk_info_2(self):
        """Test get disk_info (Normal user)"""
        with self.assertRaises(NoPermissionException):
            get_disk_info(self.normal_user)

    def test_get_environ_info_1(self):
        """Test get_environ_info"""
        data = get_environ_info(self.admin_user).model_dump()
        keys = ["os", "arch", "python"]
        data_type = [str, str, str]
        for idx, key in enumerate(keys):
            self.assertTrue(key in data)
            self.assertEqual(data_type[idx], type(data[key]))

    def test_get_environ_info_2(self):
        """Test get_environ_info (Normal user)"""
        with self.assertRaises(NoPermissionException):
            get_environ_info(self.normal_user)

    def test_get_network_info_1(self):
        """Test get_network_info"""
        data = get_network_info(self.admin_user).model_dump()
        keys = ["download_speed", "upload_speed", "downloads", "uploads"]
        data_type = [int, int, int, int]
        for idx, key in enumerate(keys):
            self.assertTrue(key in data)
            self.assertEqual(data_type[idx], type(data[key]))

    def test_get_network_info_2(self):
        """Test get_network_info (Normal user)"""
        with self.assertRaises(NoPermissionException):
            get_network_info(self.normal_user)
