import json
import logging
import mimetypes
import os
import shutil
import stat
import uuid
import zipfile

from datetime import datetime
from typing import Dict, List, Set, Tuple
from urllib.parse import quote
from wsgiref.util import FileWrapper

import epub_meta
import exifread

from django.conf import settings
from django.core.handlers.wsgi import WSGIRequest
from django.core.files.uploadedfile import (
    InMemoryUploadedFile,
    TemporaryUploadedFile,
)
from django.db import transaction
from django.db.models import Q
from django.http import HttpResponse, StreamingHttpResponse
from django.utils import timezone
from tinytag import TinyTag
from mobi import Mobi
from PyPDF2 import PdfReader

from rpidrive.controllers.compress import (
    CompressDataModel,
    create_compress_job,
)
from rpidrive.controllers.exceptions import (
    InvalidFileNameException,
    InvalidOperationRequestException,
)
from rpidrive.controllers.utils import RangeFileWrapper, range_re
from rpidrive.controllers.volume import get_root_file_id
from rpidrive.models import (
    File,
    FileKindEnum,
    Job,
    JobStatus,
    Volume,
    VolumeKindEnum,
)

logger = logging.getLogger(__name__)


class InvalidVolumeKindException(Exception):
    """Invalid volume kind exception"""


def generate_new_file_name(name: str, used_names: Set[str]):
    """Search for a filename that is not being used yet"""
    if name not in used_names:
        return name
    for i in range(1, 100000):
        name_split = name.split(".")
        name_split[-2 if len(name_split) > 1 else -1] += f" ({i})"
        new_name = ".".join(name_split)
        if new_name not in used_names:
            return new_name
    raise Exception("Filename generation run out of index!")


def get_full_path(file: File) -> str:
    """Get full path of the given file"""
    temp = file.path_from_vol
    while temp and temp[0] == os.path.sep:
        temp = temp[1:]
    if not temp:
        return file.volume.path
    return os.path.join(file.volume.path, temp)


def get_metadata(file_path: str) -> Dict:  # pylint: disable=too-many-return-statements
    """Get metadata given path"""
    if not os.path.isfile(file_path):
        return None

    media_type = mimetypes.guess_type(file_path)[0]
    if not media_type:
        return None

    try:
        if media_type.startswith("audio/") or media_type.startswith("video/"):
            return json.loads(
                str(TinyTag.get(file_path, image=True)).replace("\\u0000", "")
            )
        if media_type.startswith("image/"):
            with open(file_path, "rb") as f_h:
                img = exifread.process_file(f_h, details=False)
            return {key: str(tag_obj.values) for key, tag_obj in img.items()}
        if media_type == "application/pdf":
            with open(file_path, "rb") as f_h:
                return {
                    key: str(value) for key, value in PdfReader(f_h).metadata.items()
                }
        if media_type == "application/epub":
            return epub_meta.get_epub_metadata(file_path, read_cover_image=True)
        if media_type == "application/mobi":
            return Mobi(file_path).parse().config
    except:  # pylint: disable=bare-except
        logger.exception("Error reading metadata of %s", file_path)

    return None


def perform_index(volume: Volume):
    """Perform indexing on the volume"""
    if volume.kind != VolumeKindEnum.HOST_PATH:
        raise InvalidVolumeKindException("This volume doesn't support indexing.")

    new_files = []
    changed_files = []
    deleted_files = []
    root_file = (
        File.objects.select_related("volume")
        .prefetch_related("children")
        .get(pk=get_root_file_id(volume))
    )
    _recurse_check(
        volume,
        root_file,
        root_file.volume.path,
        new_files,
        changed_files,
        deleted_files,
    )

    File.objects.bulk_update(
        changed_files,
        fields=["last_modified", "size", "media_type", "metadata"],
        batch_size=settings.BULK_BATCH_SIZE,
    )
    File.objects.filter(pk__in=deleted_files).all().delete()

    volume.indexing = False
    volume.last_indexed = timezone.now()
    volume.save(update_fields=["indexing", "last_indexed"])


def _get_kind(file_path: str) -> FileKindEnum:
    is_dir = os.path.isdir(file_path)
    return FileKindEnum.FOLDER if is_dir else FileKindEnum.FILE


def create_entry(volume: Volume, parent: File, file_path: str) -> File:
    """Create File entry"""
    file_path = os.path.abspath(file_path)
    filename = os.path.basename(file_path)
    file_stat = os.stat(file_path)

    return File.objects.create(
        name=filename,
        kind=_get_kind(file_path),
        parent=parent,
        volume=volume,
        last_modified=datetime.fromtimestamp(file_stat.st_mtime).astimezone(
            timezone.get_current_timezone()
        ),
        size=file_stat.st_size,
        path_from_vol=file_path[len(volume.path) :],
        media_type=mimetypes.guess_type(file_path)[0],
        metadata=get_metadata(file_path),
    )


def _apply_update(file: File, file_path: str) -> bool:
    file_path = os.path.abspath(file_path)
    file_stat = os.stat(file_path)

    m_time = datetime.fromtimestamp(file_stat.st_mtime).astimezone(
        timezone.get_current_timezone()
    )
    if m_time == file.last_modified:
        return False

    existing = {
        "last_modified": file.last_modified,
        "size": file.size,
        "media_type": file.media_type,
        "metadata": file.metadata,
    }
    new = {
        "last_modified": m_time,
        "size": file_stat.st_size,
        "media_type": None,
        "metadata": None,
    }
    if os.path.isfile(file_path):
        new["media_type"] = mimetypes.guess_type(file_path)[0]
        new["metadata"] = get_metadata(file_path)

    has_change = False
    for key, value in existing.items():
        if value != new[key]:
            has_change = True
            setattr(file, key, new[key])
    return has_change


def _recurse_check(  # pylint: disable=too-many-arguments
    volume: Volume,
    root: File,
    curr_path: str,
    new: List[File],
    changed: List[File],
    delete: List[str],
):
    files_in_dir = os.listdir(curr_path)
    files_in_db = {x.name: x for x in root.children.all()}
    for filename in files_in_dir:
        full_path = os.path.join(curr_path, filename)
        # Ignore links
        if os.path.islink(full_path):
            continue

        curr_file_obj = files_in_db.get(filename, None)
        if curr_file_obj:
            del files_in_db[filename]  # Mark as found

            kind = _get_kind(full_path)
            # Different kind
            if kind != curr_file_obj.kind:
                delete.append(curr_file_obj)
                curr_file_obj = create_entry(volume, root, full_path)
                new.append(curr_file_obj)
            else:
                # Check for update
                if _apply_update(curr_file_obj, full_path):
                    changed.append(curr_file_obj)
        else:
            # Create new
            curr_file_obj = create_entry(volume, root, full_path)
            new.append(curr_file_obj)

        if os.path.isdir(full_path):
            _recurse_check(volume, curr_file_obj, full_path, new, changed, delete)

    # Add to deleted
    delete.extend([x.pk for x in files_in_db.values()])


def get_file_parents(file: File) -> List[File]:
    """Get a list of ancestor file objects to file"""
    paths = file.path_from_vol.split(os.path.sep)
    possible_paths = [os.path.sep.join(paths[:i]) for i in range(1, len(paths) + 1)]
    possible_paths[0] = "/"
    return list(
        File.objects.filter(volume_id=file.volume_id, path_from_vol__in=possible_paths)
        .order_by("path_from_vol")
        .all()
    )[:-1]


def delete_file(file: File):
    """Delete files"""
    if file.parent_id is None:
        raise InvalidOperationRequestException("Can't delete root file.")
    full_path = get_full_path(file)
    with transaction.atomic():
        if os.path.isfile(full_path):
            os.remove(full_path)
        elif os.path.isdir(full_path):
            shutil.rmtree(full_path)
        file.delete()


def rename_file(file: File, new_name: str):
    """Rename file"""
    if new_name:
        new_name = new_name.strip()
    if not new_name:
        raise InvalidFileNameException("File name can't be empty.")
    siblings = set(
        File.objects.filter(parent=file.parent)
        .exclude(pk=file.pk)
        .values_list("name", flat=True)
    )
    if new_name in siblings:
        raise InvalidFileNameException("File name is already in use.")

    parent_paths = get_full_path(file.parent).split(os.path.sep)
    new_path = os.path.abspath(os.path.join(get_full_path(file.parent), new_name))
    if parent_paths != new_path.split(os.path.sep)[:-1]:
        raise InvalidFileNameException("Invalid character in file name.")
    src_path_vol = file.path_from_vol

    shutil.move(get_full_path(file), new_path)
    file.name = new_name
    file.path_from_vol = os.path.join(file.parent.path_from_vol, new_name)
    file.save(update_fields=["name", "path_from_vol"])

    if os.path.isdir(new_path):
        children = list(
            File.objects.filter(
                volume=file.volume,
                path_from_vol__startswith=f"{src_path_vol}{os.path.sep}",
            )
            .select_for_update(of=("self",))
            .all()
        )
        for child in children:
            child.path_from_vol = (
                file.path_from_vol + child.path_from_vol[len(src_path_vol) :]
            )
        File.objects.bulk_update(
            children, fields=["path_from_vol"], batch_size=settings.BULK_BATCH_SIZE
        )


def compress_files(file_pks: List[str], parent: File, zip_name: str) -> Job:
    """Compress files"""
    if zip_name:
        zip_name = zip_name.strip()
    if not zip_name:
        raise InvalidFileNameException("Invalid file name.")

    parent_fp = get_full_path(parent)
    zip_fp = os.path.join(parent_fp, zip_name)
    if os.path.dirname(zip_fp) != parent_fp:
        raise InvalidFileNameException("Invalid file name.")

    return create_compress_job(file_pks, parent, zip_name)


def _move_file(source: File, dest: File, is_rename: bool):
    target = File.objects.filter(parent=dest, name=source.name).first()

    # Source and dest are the same (i.e. move back to same folder)
    if source == target:
        return

    init_src_path = source.path_from_vol
    init_src_path_len = len(source.path_from_vol)

    # Dest file doesn't exist.
    if not target:
        shutil.move(get_full_path(source), get_full_path(dest))
        source.parent = dest
        source.path_from_vol = os.path.join(dest.path_from_vol, source.name)
        source.volume_id = dest.volume_id
        source.save(update_fields=["parent", "path_from_vol", "volume_id"])

        # Update children
        if source.kind == FileKindEnum.FOLDER:
            children = list(
                File.objects.filter(
                    volume=source.volume_id, path_from_vol__startswith=init_src_path
                ).all()
            )
            for child in children:
                child.volume_id = dest.volume_id
                child.path_from_vol = os.path.join(
                    source.path_from_vol,
                    child.path_from_vol[init_src_path_len + 1 :],
                )
            File.objects.bulk_update(
                children,
                fields=["volume_id", "path_from_vol"],
                batch_size=settings.BULK_BATCH_SIZE,
            )
    # Both are folders, merge source into target!
    elif source.kind == target.kind == FileKindEnum.FOLDER:
        for file in File.objects.filter(parent=source).all():
            _move_file(file, target, is_rename)
        os.rmdir(get_full_path(source))
        source.delete()
    # Both are files + overwrite mode
    elif source.kind == target.kind == FileKindEnum.FILE and not is_rename:
        os.remove(get_full_path(target))
        target.delete()
        shutil.move(get_full_path(source), get_full_path(dest))
        source.parent = dest
        source.path_from_vol = os.path.join(dest.path_from_vol, source.name)
        source.volume_id = dest.volume_id
        source.save(update_fields=["parent", "path_from_vol", "volume_id"])
    else:
        # Source & dest are of different types / rename, then find a proper name and move.
        new_name = generate_new_file_name(
            source.name,
            set(File.objects.filter(parent=dest).values_list("name", flat=True)),
        )
        shutil.move(get_full_path(source), os.path.join(get_full_path(dest), new_name))
        source.name = new_name
        source.parent = dest
        source.volume_id = dest.volume_id
        source.path_from_vol = os.path.join(dest.path_from_vol, new_name)
        source.save(update_fields=["parent", "path_from_vol", "volume_id", "name"])

        if source.kind == FileKindEnum.FOLDER:
            children = list(
                File.objects.filter(
                    volume=source.volume_id, path_from_vol__startswith=init_src_path
                ).all()
            )
            for child in children:
                child.volume_id = dest.volume_id
                child.path_from_vol = os.path.join(
                    dest.path_from_vol,
                    new_name,
                    child.path_from_vol[init_src_path_len + 1 :],
                )


def move_files(file_pks: List[str], parent: File, is_rename: bool):
    """Move files"""
    if parent.kind != FileKindEnum.FOLDER:
        raise InvalidOperationRequestException("Destination must be a folder.")

    files = File.objects.filter(pk__in=file_pks).select_for_update(of=("self",)).all()
    parent_fp = get_full_path(parent)
    for file in files:
        f_p = get_full_path(file)
        if parent_fp.startswith(f_p):
            raise InvalidOperationRequestException("Invalid parent path.")

    for file in files:
        with transaction.atomic():
            _move_file(file, parent, is_rename)


def create_folder(parent: File, name: str, exists_ok=False) -> File:
    """Create folder"""
    if name:
        name = name.strip()
    if not name:
        raise InvalidFileNameException("Folder name can't be empty.")
    dup_entry = File.objects.filter(Q(parent=parent) & Q(name=name)).first()
    if dup_entry:
        if exists_ok:
            return dup_entry
        raise InvalidFileNameException("Folder name is already in use.")

    parent_paths = get_full_path(parent).split(os.path.sep)
    folder_path = os.path.abspath(os.path.join(get_full_path(parent), name))
    if parent_paths != folder_path.split(os.path.sep)[:-1]:
        raise InvalidFileNameException("Invalid character in folder name.")
    os.makedirs(folder_path, exist_ok=True)
    file_stat = os.stat(folder_path)
    folder = File.objects.create(
        name=name,
        kind=FileKindEnum.FOLDER,
        parent=parent,
        volume=parent.volume,
        last_modified=datetime.fromtimestamp(file_stat.st_mtime).astimezone(
            timezone.get_current_timezone()
        ),
        size=file_stat.st_size,
        path_from_vol=os.path.join(parent.path_from_vol, name),
    )
    return folder


def serve_file(file: File, request: WSGIRequest) -> StreamingHttpResponse:
    """Serve file"""
    file_path = get_full_path(file)
    range_header = request.META.get("HTTP_RANGE", "").strip()
    range_match = range_re.match(range_header)
    size = os.path.getsize(get_full_path(file))

    content_type = "application/octet-stream"
    if range_match:  # Handle partial file, i.e. seeking audio/video
        first_byte, last_byte = range_match.groups()
        first_byte = int(first_byte) if first_byte else 0
        last_byte = int(last_byte) if last_byte else size - 1
        if last_byte >= size:
            last_byte = size - 1
        length = last_byte - first_byte + 1
        resp = StreamingHttpResponse(
            RangeFileWrapper(
                open(file_path, "rb"),  # pylint: disable=consider-using-with
                offset=first_byte,
                length=length,
            ),
            status=206,
            content_type=content_type,
        )
        resp["Content-Length"] = str(length)
        resp["Content-Range"] = f"bytes {first_byte}-{last_byte}/{size}"
    else:  # Handle full file
        resp = StreamingHttpResponse(
            FileWrapper(open(file_path, "rb")),  # pylint: disable=consider-using-with
            content_type=content_type,
        )
        resp["Content-Length"] = str(size)

    # Fill in extra HTTP headers
    filename = os.path.basename(file_path)
    try:
        filename.encode("ascii")
        filename = f'filename="{filename}"'
    except:  # pylint: disable=bare-except
        filename = f"filename*=utf-8''{quote(filename)}"
    resp["Content-Disposition"] = f"attachment;{filename}"
    resp["Accept-Ranges"] = "bytes"

    return resp


def serve_file_thumbnail(file: File) -> HttpResponse:
    """Serve file thumbail"""
    if file.media_type.startswith("audio/"):
        return HttpResponse(
            TinyTag.get(get_full_path(file), image=True).get_image(),
            content_type="image/jpg",
        )
    return HttpResponse()


def _do_compress_files(files: List[File]) -> Tuple[str, int]:
    """Process compress job"""
    paths = [get_full_path(x) for x in files]
    total_files = 0
    while paths:
        path = paths.pop()
        total_files += 1
        if not os.path.isdir(path):
            continue
        for child in os.listdir(path):
            paths.append(os.path.join(path, child))

    zip_path = os.path.join(
        settings.ROOT_CONFIG.web.temp_dir, f"{uuid.uuid4()}.zip"
    )  # pylint: disable=protected-access
    with zipfile.ZipFile(
        zip_path, mode="w", compression=zipfile.ZIP_DEFLATED, compresslevel=9
    ) as archive:
        root_path_len = len(get_full_path(files[0].parent))
        paths = [get_full_path(x) for x in files]
        curr_files = 0
        while paths:
            path = paths.pop()
            yield path, int((curr_files / total_files) * 100)
            archive.write(path, arcname=path[root_path_len:])
            curr_files = curr_files + 1
            yield path, int((curr_files / total_files) * 100)
            if not os.path.isdir(path):
                continue
            if path.endswith(os.path.sep):
                path = path[:-1]
            for child in os.listdir(path):
                paths.append(os.path.join(path, child))
    yield zip_path, 100


def process_compress_job(job: Job) -> File:
    """Process compress job"""
    data = CompressDataModel.model_validate(job.data)
    job.status = JobStatus.RUNNING
    job.save(update_fields=["status"])
    try:
        temp_zip = None
        parent_file = File.objects.get(pk=data.parent)
        file_objs = File.objects.filter(pk__in=data.files).all()
        for file, prog in _do_compress_files(file_objs):
            job.progress = prog
            job.save(update_fields=["progress"])
            temp_zip = file

        final_path = os.path.join(get_full_path(parent_file), data.name)
        if os.path.exists(final_path):
            File.objects.filter(
                Q(name=data.name) & Q(parent=parent_file)
            ).all().delete()
            if os.path.isdir(final_path):
                shutil.rmtree(final_path)
            elif os.path.isfile(final_path):
                os.chmod(final_path, stat.S_IWRITE)
                os.remove(final_path)

        shutil.move(temp_zip, final_path)
        output_file = File.objects.create(
            name=data.name,
            kind=FileKindEnum.FILE,
            parent=parent_file,
            volume=parent_file.volume,
            path_from_vol=os.path.join(parent_file.path_from_vol, data.name),
            media_type="application/zip",
            last_modified=timezone.now(),
            size=os.path.getsize(final_path),
        )
    except (KeyboardInterrupt, SystemExit) as exc:
        raise exc
    except:  # pylint: disable=bare-except
        logger.exception("Failed zip file creation")

    job.status = JobStatus.COMPLETED
    job.save(update_fields=["status"])
    return output_file


def create_files(parent: File, files: List):
    """Create files"""
    for file in files:
        request_file = file["file"]
        request_paths: List[str] = file["path"].split(os.path.sep)[:-1]

        curr_parent = parent
        for path in request_paths:
            curr_parent = create_folder(curr_parent, path, True)
        sibling_names = set(curr_parent.children.values_list("name", flat=True))
        filename = generate_new_file_name(request_file.name, sibling_names)
        dest_fp = os.path.join(get_full_path(curr_parent), filename)
        if isinstance(request_file, InMemoryUploadedFile):
            with open(dest_fp, "wb+") as f_h:
                for chunk in request_file.chunks():
                    f_h.write(chunk)
        elif isinstance(request_file, TemporaryUploadedFile):
            shutil.move(request_file.temporary_file_path(), dest_fp)
        else:
            raise InvalidOperationRequestException("Unknown upload handler.")

        os.chmod(dest_fp, 0o755)
        create_entry(parent.volume, curr_parent, dest_fp)
