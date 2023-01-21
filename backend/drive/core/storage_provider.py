from typing import Tuple

from ..models import (
    StorageProvider,
    LocalFileObject,
    FileObjectTypeEnum,
)

def create_storage_provider_helper(
    name: str, sp_type: str, path:str
) -> Tuple[StorageProvider, LocalFileObject]:
    """Helper for creating a new storage provider"""
    s_p = StorageProvider.objects.create(
        name=name,
        type=sp_type,
        path=path,
        indexing=True,
    )
    file_obj = LocalFileObject.objects.create(
        name=name,
        obj_type=FileObjectTypeEnum.FOLDER,
        storage_provider=s_p,
        rel_path=''
    )

    return s_p, file_obj
