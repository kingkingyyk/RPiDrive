import os
import shutil
import tempfile
import uuid

from django.contrib.auth.models import User
from rpidrive.controllers.volume import create_volume
from rpidrive.models import File, VolumeKindEnum


class SetupContext:
    """Setup context"""

    def __init__(self):
        self.id = str(uuid.uuid4())
        self.root_path = os.path.join(tempfile.gettempdir(), self.id)
        os.makedirs(self.root_path)
        self.admin = User.objects.create_superuser(f"admin-{self.id}")

        self.volume = create_volume(
            self.admin, f"vol-{self.id}", VolumeKindEnum.HOST_PATH, self.root_path
        )
        self.root_file = File.objects.get(name="", volume=self.volume)

    def cleanup(self):
        """Perform cleanup"""
        self.volume.delete()
        if os.path.exists(self.root_path):
            shutil.rmtree(self.root_path)
        self.admin.delete()
