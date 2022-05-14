import os
from pathlib import Path
from ..models import StorageProvider, LocalFileObject, FileObjectType

def create_storage_provider_helper(name, sp_type, path):
    """Helper for creating a new storage provider"""
    if path.endswith(os.path.sep):
        path = path[:-1]

    # Make sure the children of the path is not a storage provider yet
    if StorageProvider.objects.filter(path__startswith=path).exists():
        raise Exception('The subfolder of this path is already added.')

    # Make sure the parent of the path is not a storage provider yet
    p_obj = Path(path)
    parents = {str(p_obj)}
    while p_obj != p_obj.parent:
        p_obj = p_obj.parent
        parents.add(str(p_obj))

    if StorageProvider.objects.filter(path__in=parents).exists():
        raise Exception('The parent folder of this path is already added.')

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
