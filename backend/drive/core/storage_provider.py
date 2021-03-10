import os
from ..models import StorageProvider, LocalFileObject, FileObjectType

def create_storage_provider_helper(name, sp_type, path):
    """Helper for creating a new storage provider"""
    if path.endswith(os.path.sep):
        path = path[:-1]

    if StorageProvider.objects.filter(path__startswith=path).exists():
        raise Exception('There is already a storage provider with path.')

    if not os.path.exists(path):
        raise Exception('Path not found!')

    s_p = StorageProvider(
        name=name,
        type=sp_type,
        path=path
    )
    s_p.save()

    file_obj = LocalFileObject(name=name,
                               obj_type=FileObjectType.FOLDER,
                               storage_provider=s_p,
                               rel_path='')
    file_obj.save()
    return s_p, file_obj
