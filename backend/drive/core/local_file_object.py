import mimetypes
import os
import shutil
import uuid
import zipfile

from typing import Iterable
from urllib.parse import quote
from wsgiref.util import FileWrapper

from django.conf import settings
from django.http import StreamingHttpResponse

from ..request_models import MoveFileStrategy
from ..models import LocalFileObject, FileObjectType
from ..utils.indexer import Metadata
from ..utils.range_file_wrapper import range_re, RangeFileWrapper

def generate_new_file_name(name, used_names):
    """Search for a filename that is not being used yet"""
    for i in range(1, 100000):
        name_split = name.split('.')
        name_split[-2 if len(name_split) > 1 else -1] += ' ({})'.format(i)
        new_name = '.'.join(name_split)
        if new_name not in used_names:
            return new_name
    raise Exception('Filename generation run out of index!')


def move_file(src: LocalFileObject,
              dest: LocalFileObject,
              strategy: str):
    """Move file and update database"""
    old_src_storage_provider = src.storage_provider
    target = LocalFileObject.objects.filter(
        storage_provider=dest.storage_provider,
        parent=dest, name=src.name).first()
    simple_update = False

    # Not exist
    old_rel_path = src.rel_path
    if not target:
        shutil.move(src.full_path, dest.full_path)
        old_rel_path = src.rel_path
        src.parent = dest
        src.rel_path = os.path.join(dest.rel_path, src.name)
        src.storage_provider = dest.storage_provider
        src.save(update_fields=['parent', 'rel_path', 'storage_provider'])
        simple_update = True
    # Exist
    else:
        # Rename if src != target type or when (both are files + strategy is rename)
        rename = src.obj_type != target.obj_type or (
            src.obj_type == FileObjectType.FILE and strategy == MoveFileStrategy.RENAME)
        if rename:
            dest_sibling_names = LocalFileObject.objects.filter(
                storage_provider=dest.storage_provider,
                parent=dest).values_list('name', flat=True)
            new_name = generate_new_file_name(src.name, dest_sibling_names)
            shutil.move(src.full_path, os.path.join(dest.full_path, new_name))
            src.parent = dest
            src.storage_provider = target.storage_provider
            src.name = new_name
            src.rel_path = os.path.join(dest.rel_path, src.name)
            src.save(update_fields=['parent', 'rel_path', 'storage_provider', 'name'])
            simple_update = True
        # Both src and target are files, overwrite.
        elif src.obj_type == FileObjectType.FILE and strategy == MoveFileStrategy.OVERWRITE:
            shutil.move(src.full_path, target.full_path)
            src.parent = dest
            src.storage_provider = target.storage_provider
            src.rel_path = os.path.join(dest.rel_path, src.name)
            src.save(update_fields=['parent', 'rel_path', 'storage_provider'])
            target.delete()
            simple_update = True
        # Both src and target are folders, merge content.
        else:
            curr_src_children = LocalFileObject.objects.filter(
                parent=src
            ).all()
            for child in curr_src_children:
                move_file(child, target, strategy)

            os.rmdir(src.full_path)
            src.delete()

    if src.obj_type == FileObjectType.FOLDER and simple_update:
        children = []
        for child in LocalFileObject.objects.filter(
            storage_provider=old_src_storage_provider, parent=src):
            child.rel_path = src.rel_path + child.rel_path[len(old_rel_path):]
            child.storage_provider = src.storage_provider
            children.append(child)
        LocalFileObject.objects.bulk_update(children, fields=['rel_path', 'storage_provider'])


def serve(request, file_path: str):
    """Serve file to HTTP request"""
    range_header = request.META.get('HTTP_RANGE', '').strip()
    range_match = range_re.match(range_header)
    size = os.path.getsize(file_path)

    content_type = mimetypes.guess_type(file_path)[0]
    content_type = 'application/octet-stream'
    if range_match:
        first_byte, last_byte = range_match.groups()
        first_byte = int(first_byte) if first_byte else 0
        last_byte = int(last_byte) if last_byte else size - 1
        if last_byte >= size:
            last_byte = size - 1
        length = last_byte - first_byte + 1
        resp = StreamingHttpResponse(
            RangeFileWrapper(open(file_path, 'rb'),
                             offset=first_byte,
                             length=length),
            status=206, content_type=content_type)
        resp['Content-Length'] = str(length)
        resp['Content-Range'] = 'bytes %s-%s/%s' % (
            first_byte, last_byte, size)
    else:
        resp = StreamingHttpResponse(FileWrapper(
            open(file_path, 'rb')), content_type=content_type)
        resp['Content-Length'] = str(size)
    f_n = os.path.basename(file_path)
    try:
        f_n.encode('ascii')
        f_n = 'filename="{}"'.format(f_n)
    except: #pylint: disable=bare-except
        f_n = "filename*=utf-8''{}".format(quote(f_n))
    resp['Content-Disposition'] = 'attachment; '+f_n
    resp['Accept-Ranges'] = 'bytes'
    return resp

def update_file_metadata(file: LocalFileObject):
    """Save file metadata if missing"""
    if file.metadata is None:
        file.metadata = Metadata.extract(file)
        LocalFileObject.objects.filter(pk=file.pk).update(metadata=file.metadata)

def zip_files(files: Iterable[LocalFileObject]) -> str:
    """Create a temp zip file and return the path"""
    total_files = 0
    paths = [x.full_path for x in files]
    while paths:
        path = paths.pop()
        total_files += 1
        if not os.path.isdir(path):
            continue
        for child in os.listdir(path):
            paths.append(os.path.join(path, child))

    zip_path = os.path.join(settings._TEMP_DIR, f'{uuid.uuid4()}.zip') # pylint: disable=protected-access
    with zipfile.ZipFile(
        zip_path, mode='w',
        compression=zipfile.ZIP_DEFLATED,
        compresslevel=9
    ) as archive:
        root_path_len = len(files[0].parent.full_path)
        paths = [x.full_path for x in files]
        curr_files = 0
        while paths:
            path = paths.pop()
            yield path, int((curr_files / total_files) * 100)
            archive.write(path, arcname=path[root_path_len:])
            curr_files = curr_files + 1
            yield path, int((curr_files / total_files) * 100)
            if not os.path.isdir(path):
                continue
            for child in os.listdir(path):
                paths.append(os.path.join(path, child))
    yield zip_path, 100
