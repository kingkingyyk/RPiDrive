from datetime import timedelta
from typing import List

from django.conf import settings
from django.contrib.auth.models import User
from django.core.handlers.wsgi import WSGIRequest
from django.db import transaction
from django.db.models import Q, QuerySet
from django.http import HttpResponse, StreamingHttpResponse
from django.utils import timezone

from rpidrive.controllers.exceptions import (
    InvalidFileNameException,
    InvalidOperationRequestException,
)
from rpidrive.controllers.local_file import (
    compress_files as local_compress_files,
    create_files as local_create_files,
    create_folder as local_create_folder,
    delete_file as local_delete_file,
    get_file_parents as local_get_file_parents,
    get_full_path as local_get_full_path,
    move_files as local_move_files,
    rename_file as local_rename_file,
    serve_file as local_serve_file,
    serve_file_thumbnail as local_serve_file_thumbnail,
)
from rpidrive.controllers.volume import (
    get_volumes,
    request_volume,
    NoPermissionException,
    VolumeNotFoundException,
    VolumePermissionEnum,
)
from rpidrive.models import (
    File,
    FileKindEnum,
    PublicFileLink,
    Volume,
    VolumeKindEnum,
)


class FileNotFoundException(Exception):
    """File not found exception"""


def get_file(
    user: User,
    file_pk: str,
    select_related: List[str] = None,
    prefetch_related: List[str] = None,
    write: bool = False,
) -> File:
    """Get file by id"""
    if not select_related:
        select_related = []
    if not prefetch_related:
        prefetch_related = []

    file = (
        File.objects.filter(pk=file_pk)
        .select_related(*select_related)
        .prefetch_related(*prefetch_related)
    )
    if write:
        file = file.select_for_update(of=("self",))
    file = file.first()

    # Check file existence
    if not file:
        raise FileNotFoundException("File not found.")

    # Check permission
    try:
        request_volume(
            user,
            file.volume_id,
            VolumePermissionEnum.READ if not write else VolumePermissionEnum.READ_WRITE,
            write,
        )
    except (
        NoPermissionException,
        VolumeNotFoundException,
    ):
        raise FileNotFoundException(  # pylint: disable=raise-missing-from
            "File not found."
        )

    return file


def get_file_parents(file: File) -> List[File]:
    """Get a list of ancestor file objects to file"""
    if file.volume.kind == VolumeKindEnum.HOST_PATH:
        return local_get_file_parents(file)
    raise NotImplementedError()


def delete_files(user: User, file_pks: List[str]):
    """Delete file"""
    volume_pks = list(
        File.objects.filter(pk__in=file_pks)
        .values_list("volume_id", flat=True)
        .distinct()
    )
    if len(volume_pks) != 1:
        raise InvalidOperationRequestException(
            "Files & destination must be in the same volume"
        )
    volume_id = volume_pks[0]
    if Volume.objects.get(pk=volume_id).kind != VolumeKindEnum.HOST_PATH:
        raise NotImplementedError()

    for file_pk in file_pks:
        with transaction.atomic():
            file = get_file(user, file_pk, ["volume"], [], True)
            local_delete_file(file)


def rename_file(user: User, file_pk: str, new_name: str):
    """Rename file"""
    if not new_name:
        raise InvalidFileNameException("Invalid file name.")

    with transaction.atomic():
        file = get_file(user, file_pk, ["parent", "volume"], [], True)
        if file.volume.kind == VolumeKindEnum.HOST_PATH:
            local_rename_file(file, new_name)
        else:
            raise NotImplementedError()


def compress_files(user: User, file_pks: List[str], parent_pk: str, zip_name: str):
    """Compress files"""
    zip_name = zip_name.strip()
    if not zip_name:
        raise InvalidFileNameException("Invalid file name.")
    if not zip_name.lower().endswith(".zip"):
        zip_name += ".zip"

    if not file_pks:
        raise InvalidOperationRequestException("No file to compress.")
    if File.objects.filter(pk__in=file_pks).count() != len(file_pks):
        raise InvalidOperationRequestException("Invalid file to compress.")

    all_files = file_pks + [parent_pk]
    volume_pks = list(
        File.objects.filter(pk__in=all_files)
        .values_list("volume_id", flat=True)
        .distinct()
    )
    if len(volume_pks) != 1:
        raise InvalidOperationRequestException(
            "Files & destination must be in the same volume"
        )

    with transaction.atomic():
        volume = request_volume(
            user, volume_pks[0], VolumePermissionEnum.READ_WRITE, True
        )
        parent = get_file(user, parent_pk, [], [], True)
        if parent.kind != FileKindEnum.FOLDER:
            raise InvalidOperationRequestException("Can't create zip file in a file.")
        files_parent_count = (
            File.objects.filter(pk__in=file_pks)
            .values_list("parent", flat=True)
            .distinct()
            .count()
        )
        if files_parent_count != 1:
            raise InvalidOperationRequestException(
                "Only can move items in the same level!"
            )

        if volume.kind == VolumeKindEnum.HOST_PATH:
            local_compress_files(file_pks, parent, zip_name)
        else:
            raise NotImplementedError()


def move_files(user: User, file_pks: List[str], parent_pk: str, is_rename: bool):
    """Move files"""
    volume_pks = list(
        File.objects.filter(pk__in=file_pks)
        .values_list("volume_id", flat=True)
        .distinct()
    )
    if len(volume_pks) != 1:
        raise InvalidOperationRequestException("Files must be in the same volume")
    parent = File.objects.get(pk=parent_pk)

    with transaction.atomic():
        volume_p = request_volume(
            user, parent.volume_id, VolumePermissionEnum.READ_WRITE, True
        )
        if volume_p.kind != VolumeKindEnum.HOST_PATH:
            raise NotImplementedError()
        volume = request_volume(
            user, volume_pks[0], VolumePermissionEnum.READ_WRITE, True
        )
        if volume.kind != VolumeKindEnum.HOST_PATH:
            raise NotImplementedError()

        local_move_files(file_pks, parent, is_rename)


def share_file(user: User, file_pk: str) -> PublicFileLink:
    """Share file"""
    file = get_file(user, file_pk, [], [], False)
    link = PublicFileLink.objects.create(
        file=file,
        creator=user,
        expire_time=timezone.now()
        + timedelta(settings.ROOT_CONFIG.web.public_link_expiry),
    )
    return link


def create_folder(user: User, parent_pk: str, name: str) -> File:
    """Create folder"""
    with transaction.atomic():
        folder = get_file(user, parent_pk, ["parent", "volume"], [], True)
        if folder.kind != FileKindEnum.FOLDER:
            raise InvalidOperationRequestException("Can't create folder in file.")

        if folder.volume.kind == VolumeKindEnum.HOST_PATH:
            return local_create_folder(folder, name)

        raise NotImplementedError()


def serve_file(user: User, file_pk: str, request: WSGIRequest) -> StreamingHttpResponse:
    """Serve file"""
    file = get_file(user, file_pk, ["volume"], [], False)
    if file.kind == FileKindEnum.FOLDER:
        raise InvalidOperationRequestException("Can't download folder.")
    if file.volume.kind == VolumeKindEnum.HOST_PATH:
        return local_serve_file(file, request)

    raise NotImplementedError()


def serve_qa_file(qa_id: str, request: WSGIRequest) -> StreamingHttpResponse:
    """Serve file"""
    link = (
        PublicFileLink.objects.filter(pk=qa_id)
        .select_related("file", "file__volume")
        .first()
    )
    if not link:
        raise FileNotFoundException("Key not found.")
    if link.expire_time < timezone.now():
        link.delete()
        raise FileNotFoundException("Key not found.")

    if link.file.kind == FileKindEnum.FOLDER:
        raise InvalidOperationRequestException("Can't download folder.")
    if link.file.volume.kind == VolumeKindEnum.HOST_PATH:
        return local_serve_file(link.file, request)

    raise NotImplementedError()


def serve_file_thumbnail(user: User, file_pk: str) -> HttpResponse:
    """Serve file thumbail"""
    file = get_file(user, file_pk, ["volume"], [], False)
    if file.kind == FileKindEnum.FOLDER:
        raise InvalidOperationRequestException("Can't download folder.")
    if file.volume.kind == VolumeKindEnum.HOST_PATH:
        return local_serve_file_thumbnail(file)

    raise NotImplementedError()


def create_files(user: User, parent_pk: str, files: List):
    """Create files"""
    with transaction.atomic():
        parent = get_file(user, parent_pk, ["volume"], ["children"], True)
        if parent.kind == FileKindEnum.FILE:
            raise InvalidOperationRequestException("Unable to upload files to file")

        if parent.volume.kind == VolumeKindEnum.HOST_PATH:
            local_create_files(parent, files)
            return

    raise NotImplementedError()


def search_files(user: User, keyword: str) -> QuerySet:
    """Search file"""
    volume_pks = get_volumes(user).values_list("pk", flat=True)
    return File.objects.filter(Q(volume_id__in=volume_pks) & Q(name__search=keyword))


def get_file_full_path(file: File):
    """Get file full path"""
    if file.volume.kind == VolumeKindEnum.HOST_PATH:
        return local_get_full_path(file)

    raise NotImplementedError()
