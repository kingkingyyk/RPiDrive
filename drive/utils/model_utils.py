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
                folder = Folder(relative_path='',
                                last_modified=datetime.strptime(
                                    time.ctime(os.path.getmtime(os.path.join(ModelUtils.get_storage().base_path))),
                                    "%a %b %d %H:%M:%S %Y"),
                                size=0)
                folder.save()
        return folder