from django.db.models.signals import pre_save
from django.dispatch import receiver
from .models import *
import os


@receiver(pre_save, sender=File)
def update_file(sender, instance, **kwargs):
    instance.name = instance.relative_path.split(os.path.sep)[-1]
    instance.file_extension = File.extract_file_extension(instance.name)


@receiver(pre_save, sender=Folder)
def update_folder(sender, instance, **kwargs):
    instance.name = instance.relative_path.split(os.path.sep)[-1]
