from ..models import *


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
                folder = Folder.objects.select_related('parent_folder').get(relative_path='')
            except:
                folder = Folder(relative_path='')
                folder.save()
        return folder


    @staticmethod
    def sync_folder(storage, folder):
        real_path = os.path.join(storage.base_path, folder.relative_path)
        db_folders = [x for x in folder.folder_set.all()]
        db_files = [x for x in folder.file_set.all()]
        fs_folder_names = [x for x in os.listdir(real_path) if os.path.isdir(os.path.join(real_path, x))]
        fs_file_names = [x for x in os.listdir(real_path) if os.path.isfile(os.path.join(real_path, x))]

        # Lazy delete file record if needed
        for f in [x for x in db_folders if x.name not in fs_folder_names]:
            f.delete()

        for f in [x for x in db_files if x.name not in fs_file_names]:
            f.delete()

        # Lazy create file record if needed
        db_folder_names = [x.name for x in db_folders]
        [Folder(relative_path=os.path.join(folder.relative_path, x),
                parent_folder=folder).save()
         for x in fs_folder_names if x not in db_folder_names]

        db_file_names = [x.name for x in db_files]
        [File(relative_path=os.path.join(folder.relative_path, x),
              parent_folder=folder).save()
         for x in fs_file_names if x not in db_file_names]

    @staticmethod
    def recursive_sync_folder(verbose=False):
        if Storage.objects.count() > 0:
            if verbose:
                print('Start synchronizing data....')
            storage = ModelUtils.get_storage()
            root_folder = ModelUtils.get_folder_by_id(None)
            folder_list = [root_folder]

            while folder_list:
                curr_folder = folder_list.pop()
                ModelUtils.sync_folder(storage, curr_folder)
                folder_list += list(curr_folder.folder_set.all())
            if verbose:
                print('Done synchronizing data!')

    @staticmethod
    def auto_create_drive():
        if Drive.objects.count() == 0:
            Drive(name='RPi Drive').save()
