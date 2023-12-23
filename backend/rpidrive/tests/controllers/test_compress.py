import os
from django.test import TestCase

from rpidrive.controllers.local_file import create_entry
from rpidrive.controllers.compress import (
    InvalidFileNameException,
    NoFileException,
    create_compress_job,
)
from rpidrive.models import JobKind, JobStatus
from rpidrive.tests.helpers.setup import SetupContext


class TestCompress(TestCase):
    """Test compress"""

    def setUp(self):
        self.context = SetupContext()
        text_fp = os.path.join(self.context.root_path, "hehe.txt")
        with open(text_fp, "w+") as f_h:
            f_h.write("a")
        self.txt_file = create_entry(
            self.context.volume, self.context.root_file, text_fp
        )

    def tearDown(self):
        self.context.cleanup()

    def test_create_compress_job(self):
        """Test create_compress_job"""
        file_name = "file.zip"
        job = create_compress_job(
            [str(self.txt_file.id)], self.context.root_file, file_name
        )
        self.assertIsNotNone(job)
        self.assertEqual(JobKind.ZIP, job.kind)
        self.assertEqual(file_name, job.description)
        self.assertEqual(
            {
                "files": [str(self.txt_file.id)],
                "parent": str(self.context.root_file.id),
                "name": file_name,
            },
            job.data,
        )
        self.assertEqual(job.volume_id, self.context.volume.id)
        self.assertEqual(JobStatus.IN_QUEUE, job.status)

    def test_create_compress_job_exc_1(self):
        """Test create_compress_job (No file - 1)"""
        with self.assertRaises(NoFileException):
            create_compress_job([], self.context.root_file, "name.zip")

    def test_create_compress_job_exc_2(self):
        """Test create_compress_job (No file - 2)"""
        with self.assertRaises(NoFileException):
            create_compress_job([], None, "name.zip")

    def test_create_compress_job_exc_3(self):
        """Test create_compress_job (Invalid name)"""
        with self.assertRaises(InvalidFileNameException):
            create_compress_job([self.context.root_file], self.context.root_file, "  ")
