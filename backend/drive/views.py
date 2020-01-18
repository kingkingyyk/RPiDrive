from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse, StreamingHttpResponse, HttpResponseBadRequest
from .models import File, FolderObject, FileObject, FileTypes, Storage, MusicFileObject, PictureFileObject
from django.db.models.functions import Lower
from .utils.connection_utils import RangeFileWrapper, range_re
from wsgiref.util import FileWrapper
from .mq.mq import MQUtils, MQChannels
import os, mimetypes

def get_child_files(request):
    def serialize_folder(f):
        return {'id': f.pk, 'name': f.name}

    def file_to_data(x):
        dat = {'id': str(x.pk),
                'name': x.name, 
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
        parent_folder = File.objects.select_related('parent_folder').get(pk=parent_folder_id)
    except:
        parent_folder = File.objects.select_related('parent_folder').get(parent_folder=None)

    files = File.objects.order_by(Lower('name'))
    if parent_folder_id:
        files = files.filter(parent_folder=parent_folder)
    files = [x for x in files if isinstance(x, FolderObject)] + [x for x in files if isinstance(x, FileObject)]
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
    f_real_path = os.path.join(storage.base_path, file.relative_path[1:])

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
        resp = StreamingHttpResponse(RangeFileWrapper(open(f_real_path, 'rb'), offset=first_byte, length=length), status=206, content_type=file.content_type)
        resp['Content-Length'] = str(length)
        resp['Content-Range'] = 'bytes %s-%s/%s' % (first_byte, last_byte, size)
    else:
        resp = StreamingHttpResponse(FileWrapper(open(f_real_path, 'rb')), content_type=file.content_type)
        resp['Content-Length'] = str(size)
    resp['Content-Disposition'] = 'filename='+file.name
    resp['Accept-Ranges'] = 'bytes'
    return resp

def create_new_folder(request, folder_id):
    storage = get_object_or_404(Storage, primary=True)
    folder = get_object_or_404(FolderObject, id=folder_id)

    new_folder_name = request.POST['name']
    new_folder_path = os.path.join(storage.base_path, folder.relative_path[1:], new_folder_name)
    if os.path.exists(new_folder_path):
        return JsonResponse({},status=500)

    try:
        MQUtils.push_to_channel(MQChannels.FOLDER_TO_CREATE, {'folder': folder.pk, 'name': new_folder_path}, True)
        return JsonResponse({}, status=201)
    except:
        return JsonResponse({}, status=500)

def upload_file(request, folder_id):
    pass

def move_file(request):
    pass

def rename_file(request):
    pass

def delete_file(request):
    pass

def add_download(request, folder_id):
    pass

def get_storage(request):
    pass

def get_system(request):
    pass