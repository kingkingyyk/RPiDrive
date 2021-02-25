from ..models import StorageProvider, LocalFileObject, FileObjectType
import os

def create_storage_provider_helper(name, type, path):
    if path.endswith(os.path.sep):
        path = path[:-1]
    
    if StorageProvider.objects.filter(path__startswith=path).exists():
        raise Exception('There is already a storage provider with path.')

    if not os.path.exists(path):
        raise Exception('Path not found!')

    sp = StorageProvider(
        name=name,
        type=type,
        path=path
    )
    sp.save()

    file_obj = LocalFileObject(name=name,
                               obj_type=FileObjectType.FOLDER,
                               storage_provider=sp,
                               rel_path='')
    file_obj.save()
    return sp, file_obj