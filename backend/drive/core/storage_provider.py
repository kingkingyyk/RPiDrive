from ..models import StorageProvider, LocalFileObject, FileObjectType
import os

def create_storage_provider_helper(name, type, path):
    if path.endswith(os.path.sep):
        path = path[:-1]

    sp = StorageProvider(
        name=name,
        type=type,
        path=path
    )
    sp.save()

    file_obj = LocalFileObject(name='<storage root>',
                               obj_type=FileObjectType.FOLDER,
                               storage_provider=sp,
                               rel_path=os.path.sep)
    file_obj.save()
    return sp