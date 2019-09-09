from ..models import *
import time


class ModelUtils:

    @staticmethod
    def get_storage():
        return Storage.objects.get(primary=True)

    @staticmethod
    def get_folder_by_id(folder_id):
        try:
            folder = Folder.objects.filter(id=folder_id).first()
        except:
            folder = None
        if folder is None:
            try:
                folder = Folder.objects.get(relative_path='')
            except:
                folder = Folder(relative_path='')
                folder.save()
        return folder