from django.db.models.signals import pre_save
from django.dispatch import receiver
from .models import *
from .utils.model_utils import ModelUtils
import os, mimetypes


@receiver(pre_save, sender=File)
def update_file(sender, instance, **kwargs):
    instance.name = instance.relative_path.split(os.path.sep)[-1]
    instance.file_extension = File.extract_file_extension(instance.name)
    instance.content_type = mimetypes.guess_type(os.path.join(ModelUtils.get_storage().base_path, instance.relative_path))[0] or 'application/octet-stream'


@receiver(pre_save, sender=Folder)
def update_folder(sender, instance, **kwargs):
    instance.name = instance.relative_path.split(os.path.sep)[-1]
