import json
import mimetypes
import os
import platform
import shutil
import traceback
from datetime import datetime
from wsgiref.util import FileWrapper

from django.db import transaction
from django.db.models.functions import Lower
from django.http import (HttpResponseBadRequest, JsonResponse,
                         StreamingHttpResponse)
from django.shortcuts import get_object_or_404, render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils.timezone import get_current_timezone

from drive.management.commands.indexer import Indexer

from ..models import (File, FileObject, FileTypes, FolderObject,
                      MusicFileObject, PictureFileObject, Storage)
from ..utils.connection_utils import RangeFileWrapper, range_re
from ..utils.file_utils import FileUtils


def get_folder_redirect(request, folder_id):
    try:
        folder = FolderObject.objects.get(pk=folder_id)
    except:
        folder = FolderObject.objects.get(parent_folder=None)
    return JsonResponse({'id': str(folder.pk)})


def get_child_files(request):
    def serialize_folder(f):
        return {'id': f.pk, 'name': f.name}

    def file_to_data(x):
        dat = {'id': str(x.pk),
               'name': x.name,
               'relative_path': x.relative_path,
               'natural_last_modified': x.natural_last_modified,
               'natural_size': x.natural_size,
               'type': x.__class__.__name__,
               'ext_type': FileTypes.get_type(x.name) if isinstance(x, FileObject) else 'FOLDER'}
        if isinstance(x, MusicFileObject):
            dat = {**dat, **{
                'title': x.title,
                'artist': x.artist,
                'album': x.album,
                'genre': x.genre,
            }}
        elif isinstance(x, PictureFileObject):
            dat = {**dat, **{
                'body_make': x.body_make,
                'body_model': x.body_model,
                'lens_make': x.lens_make,
                'lens_model': x.lens_model,
                'iso': x.iso,
                'aperture': x.aperture,
                'shutter_speed': x.shutter_speed,
                'focal_length': x.focal_length,
            }}
        return dat

    root_folder = File.objects.get(parent_folder=None)

    parent_folder_id = request.GET.get('parent-folder', None)
    parent_folder = None
    try:
        parent_folder = FolderObject.objects.select_related(
            'parent_folder').get(pk=parent_folder_id)
    except:
        parent_folder = FolderObject.objects.select_related(
            'parent_folder').get(parent_folder=None)

    files = File.objects.filter(
        parent_folder=parent_folder).order_by(Lower('name'))
    files = [x for x in files if isinstance(
        x, FolderObject)] + [x for x in files if isinstance(x, FileObject)]
    files_data = [file_to_data(x) for x in files]

    parent_folders = []
    temp = parent_folder.parent_folder
    while temp:
        parent_folders.insert(0, serialize_folder(temp))
        temp = temp.parent_folder
    if len(parent_folders) > 0:
        parent_folders = parent_folders[1:]

    data = {
        'id': parent_folder.id,
        'name': parent_folder.name,
        'parent-folders': parent_folders,
        'parent-folder': serialize_folder(parent_folder.parent_folder) if parent_folder.parent_folder else None,
        'root-folder': serialize_folder(root_folder),
        'files': files_data
    }
    return JsonResponse(data)


def get_child_filenames(request):
    parent_folder_id = request.GET.get('parent-folder', None)
    parent_folder = None
    try:
        parent_folder = FolderObject.objects.select_related(
            'parent_folder').get(pk=parent_folder_id)
    except:
        parent_folder = FolderObject.objects.select_related(
            'parent_folder').get(parent_folder=None)

    data = {'folder-name': parent_folder.name,
            'case-sensitive': os.name != 'nt',
            'filenames': [x for x in File.objects.filter(parent_folder=parent_folder).values_list('name', flat=True).all()]}
    return JsonResponse(data)


def get_child_folders(request):
    parent_folder_id = request.GET.get('parent-folder', None)
    try:
        parent_folder = FolderObject.objects.select_related(
            'parent_folder').get(pk=parent_folder_id)
    except:
        parent_folder = FolderObject.objects.select_related(
            'parent_folder').get(parent_folder=None)
    child_folders = FolderObject.objects.filter(
        parent_folder=parent_folder).order_by('name').all()
    data = {
        'id': str(parent_folder.id),
        'name': str(parent_folder.name),
        'parent-folder': str(parent_folder.parent_folder.pk) if parent_folder.parent_folder else None,
        'folders': [{'id': str(x.pk), 'name': str(x.name)} for x in child_folders]
    }
    return JsonResponse(data)


def get_storages(request):
    storages = Storage.objects.order_by('primary', 'base_path').all()
    data = [{
        'base-path': x.base_path,
        'primary': x.primary,
        'natural-total-space': x.total_space_natural,
        'natural-used-space': x.used_space_natural,
        'used-space-percent': int((float(x.used_space)/x.total_space)*100),

    } for x in storages]
    return JsonResponse(data, safe=False)


def download(request, file_id):
    storage = get_object_or_404(Storage, primary=True)
    file = get_object_or_404(File, id=file_id)
    f_real_path = os.path.join(storage.base_path, file.relative_path)

    range_header = request.META.get('HTTP_RANGE', '').strip()
    range_match = range_re.match(range_header)
    size = os.path.getsize(f_real_path)
    if range_match:
        first_byte, last_byte = range_match.groups()
        first_byte = int(first_byte) if first_byte else 0
        last_byte = int(last_byte) if last_byte else size - 1
        if last_byte >= size:
            last_byte = size - 1
        length = last_byte - first_byte + 1
        resp = StreamingHttpResponse(RangeFileWrapper(open(
            f_real_path, 'rb'), offset=first_byte, length=length), status=206, content_type=file.content_type)
        resp['Content-Length'] = str(length)
        resp['Content-Range'] = 'bytes %s-%s/%s' % (
            first_byte, last_byte, size)
    else:
        resp = StreamingHttpResponse(FileWrapper(
            open(f_real_path, 'rb')), content_type=file.content_type)
        resp['Content-Length'] = str(size)
    resp['Content-Disposition'] = 'filename='+file.name
    resp['Accept-Ranges'] = 'bytes'
    return resp


@require_http_methods(["POST"])
@csrf_exempt
@transaction.atomic
def create_new_folder(request):
    data = json.loads(request.body)
    storage = get_object_or_404(Storage.objects.select_for_update(), primary=True)
    parent_folder = get_object_or_404(FolderObject.objects.select_for_update(), id=data['folder-id'])

    new_folder_name = data.get('name', None)
    if not new_folder_name:
        return JsonResponse({}, status=400)

    new_folder_path = os.path.join(
        storage.base_path, parent_folder.relative_path, new_folder_name)

    try:
        if not os.path.exists(new_folder_path):
            os.mkdir(new_folder_path)
        new_folder_rel_path = new_folder_path[len(storage.base_path)+1:]
        if not FolderObject.objects.filter(relative_path=new_folder_rel_path).exists():
            FolderObject(name=new_folder_name, relative_path=new_folder_rel_path,
                        parent_folder=parent_folder,
                        last_modified=datetime.fromtimestamp(os.path.getmtime(new_folder_path), tz=get_current_timezone())).save()
        return JsonResponse({})
    except:
        print(traceback.format_exc())
        return JsonResponse({}, status=500)


@require_http_methods(["POST"])
@csrf_exempt
@transaction.atomic
def upload_file(request, folder_id):
    storage = Storage.objects.get(primary=True)
    parent_folder = get_object_or_404(FolderObject.objects.select_for_update(), pk=folder_id)
    form = 'files'
    if request.FILES[form]:
        for temp_file in request.FILES.getlist(form):
            f_real_path = os.path.join(
                storage.base_path, parent_folder.relative_path, temp_file.name)
            if os.path.exists(f_real_path):
                FileUtils.delete_file_or_dir(f_real_path)
            with open(f_real_path, 'wb+') as f:
                shutil.copyfileobj(temp_file.file, f, 10485760)

            Indexer().update_file(storage.base_path, parent_folder, f_real_path)
    return JsonResponse({})

@require_http_methods(["POST"])
@csrf_exempt
@transaction.atomic
def move_files(request, folder_id):
    storage = get_object_or_404(Storage, primary=True)
    folder = get_object_or_404(FolderObject, pk=folder_id)
    file_list = json.loads(request.body)
    parent_folder_ids = []
    for file_id in file_list:
        temp_file = File.objects.select_related(
            'parent_folder').get(pk=file_id)
        while temp_file is not None:
            parent_folder_ids.append(temp_file.id)
            temp_file = temp_file.parent_folder

    if str(folder.id) not in parent_folder_ids:
        files = File.objects.select_for_update().filter(pk__in=file_list).all()
        for f in files:
            old_path = os.path.join(storage.base_path, f.relative_path)
            new_path = os.path.join(
                storage.base_path, folder.relative_path, f.name)

            postfix_count = 1
            while os.path.exists(new_path):
                fname_split = f.name.split('.')
                if len(fname_split) == 1:
                    fname_split[-1] = fname_split[-1] + \
                        '_' + str(postfix_count)
                else:
                    fname_split[-2] = fname_split[-2] + \
                        '_' + str(postfix_count)
                new_fname = '.'.join(fname_split)
                new_path = os.path.join(
                    storage.base_path, folder.relative_path, new_fname)
                postfix_count += 1

            os.rename(old_path, new_path)
            f.relative_path = new_path[len(storage.base_path)+1:]
            f.name = os.path.basename(new_path)
            f.parent_folder = folder
            f.save()

            if isinstance(f, FolderObject):
                Indexer().update_relative_path(storage.base_path, f)

        return JsonResponse({})
    else:
        return JsonResponse({}, status=400)

@require_http_methods(["POST"])
@csrf_exempt
@transaction.atomic
def rename_file(request, file_id):
    storage = Storage.objects.select_for_update().get(primary=True)
    file = File.objects.select_related().select_for_update().get(pk=file_id)
    data = json.loads(request.body)
    new_name = data.get('name', '')
    if file.name != new_name and len(new_name) > 0:
        existing_path = os.path.join(storage.base_path, file.relative_path)
        new_path = os.path.join(storage.base_path, file.parent_folder.relative_path, new_name)
        os.rename(existing_path, new_path)

        file.name = new_name
        if len(file.parent_folder.relative_path) > 0:
            file.relative_path = file.parent_folder.relative_path + os.path.sep + file.name
        else:
            file.relative_path = file.parent_folder.relative_path + file.name
        file.save()

        if isinstance(file, FolderObject):
            Indexer().update_relative_path(storage.base_path, file)
        return JsonResponse({})
    else:
        return JsonResponse({}, status=400)

@require_http_methods(["POST"])
@csrf_exempt
@transaction.atomic
def delete_files(request):
    file_list = json.loads(request.body)
    storage = Storage.objects.select_for_update().get(primary=True)
    with transaction.atomic():
        file_list = File.objects.select_for_update().filter(pk__in=file_list).all()
        for f in file_list:
            try:
                FileUtils.delete_file_or_dir(os.path.join(
                    storage.base_path, f.relative_path))
                f.delete()
            except:
                print(traceback.format_exc())
    return JsonResponse({}, status=200)


def add_download(request, folder_id):
    pass
