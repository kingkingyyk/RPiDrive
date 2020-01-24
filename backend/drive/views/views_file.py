from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse, StreamingHttpResponse, HttpResponseBadRequest
from ..models import File, FolderObject, FileObject, FileTypes, Storage, MusicFileObject, PictureFileObject
from django.db.models.functions import Lower
from ..utils.connection_utils import RangeFileWrapper, range_re
from wsgiref.util import FileWrapper
from ..mq.mq import MQUtils, MQChannels
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from ..utils.file_utils import FileUtils
import os, mimetypes, platform, json, shutil

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
        parent_folder = FolderObject.objects.select_related('parent_folder').get(pk=parent_folder_id)
    except:
        parent_folder = FolderObject.objects.select_related('parent_folder').get(parent_folder=None)

    files = File.objects.filter(parent_folder=parent_folder).order_by(Lower('name'))
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

def get_child_filenames(request):
    parent_folder_id = request.GET.get('parent-folder', None)
    parent_folder = None
    try:
        parent_folder = FolderObject.objects.select_related('parent_folder').get(pk=parent_folder_id)
    except:
        parent_folder = FolderObject.objects.select_related('parent_folder').get(parent_folder=None)

    data = {'folder-name': parent_folder.name, 
            'case-sensitive': os.name != 'nt',
            'filenames': [x for x in File.objects.filter(parent_folder=parent_folder).values_list('name', flat=True).all()]}
    return JsonResponse(data)

def get_child_folders(request):
    parent_folder_id = request.GET.get('parent-folder', None)
    try:
        parent_folder = FolderObject.objects.select_related('parent_folder').get(pk=parent_folder_id)
    except:
        parent_folder = FolderObject.objects.select_related('parent_folder').get(parent_folder=None)
    child_folders = FolderObject.objects.filter(parent_folder=parent_folder).order_by('name').all()
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
        resp = StreamingHttpResponse(RangeFileWrapper(open(f_real_path, 'rb'), offset=first_byte, length=length), status=206, content_type=file.content_type)
        resp['Content-Length'] = str(length)
        resp['Content-Range'] = 'bytes %s-%s/%s' % (first_byte, last_byte, size)
    else:
        resp = StreamingHttpResponse(FileWrapper(open(f_real_path, 'rb')), content_type=file.content_type)
        resp['Content-Length'] = str(size)
    resp['Content-Disposition'] = 'filename='+file.name
    resp['Accept-Ranges'] = 'bytes'
    return resp

@require_http_methods(["POST"])
@csrf_exempt 
def create_new_folder(request):
    data = json.loads(request.body)
    storage = get_object_or_404(Storage, primary=True)
    folder = get_object_or_404(FolderObject, id=data['folder-id'])

    new_folder_name = data['name']
    new_folder_path = os.path.join(storage.base_path, folder.relative_path, new_folder_name)
    if os.path.exists(new_folder_path):
        return JsonResponse({},status=500)

    try:
        MQUtils.push_to_channel(MQChannels.FOLDER_OBJ_TO_CREATE, {'folder': str(folder.pk), 'name': new_folder_path}, True)
        return JsonResponse({}, status=201)
    except:
        import traceback
        print(traceback.format_exc())
        return JsonResponse({}, status=500)

@require_http_methods(["POST"])
@csrf_exempt 
def upload_file(request, folder_id):
    storage = Storage.objects.get(primary=True)
    folder = get_object_or_404(FolderObject, pk=folder_id)
    form = 'files'
    stored_fp = []
    if request.FILES[form]:
        for temp_file in request.FILES.getlist(form):
            f_real_path = os.path.join(storage.base_path, folder.relative_path, temp_file.name)
            if os.path.exists(f_real_path):
                FileUtils.delete_file_or_dir(f_real_path)
            with open(f_real_path, 'wb+') as f:
                shutil.copyfileobj(temp_file.file, f, 10485760)
            stored_fp.append(f_real_path)
    try:
        MQUtils.push_to_channel(MQChannels.REINDEX_FOLDER, {'folder': str(folder.pk), 'files': stored_fp}, True, timeout=5.0*len(stored_fp))
        return JsonResponse({}, status=201)
    except:
        import traceback
        print(traceback.format_exc())
        return JsonResponse({}, status=500)

@require_http_methods(["POST"])
@csrf_exempt 
def move_files(request, folder_id):
    folder = get_object_or_404(FolderObject, pk=folder_id)
    file_list = json.loads(request.body)
    parent_folder_ids = []
    for file_id in file_list:
        temp_file = File.objects.select_related('parent_folder').get(pk=file_id)
        while temp_file is not None:
            parent_folder_ids.append(temp_file.id)
            temp_file = temp_file.parent_folder

    if str(folder.id) not in parent_folder_ids:
        try:
            MQUtils.push_to_channel(MQChannels.FILE_TO_MOVE, {'folder': str(folder.pk), 'files': file_list}, True)
            return JsonResponse({}, status=200)
        except:
            import traceback
            print(traceback.format_exc())
    return JsonResponse({}, status=500)


@require_http_methods(["POST"])
@csrf_exempt 
def rename_file(request, file_id):
    file = get_object_or_404(File, pk=file_id)
    data = json.loads(request.body)
    name = data.get('name', '')
    if name != '':
        try:
            MQUtils.push_to_channel(MQChannels.FILE_TO_RENAME, {'file': str(file.pk), 'name': name}, True)
            return JsonResponse({}, status=200)
        except:
            import traceback
            print(traceback.format_exc())
    return JsonResponse({}, status=500)

@require_http_methods(["POST"])
@csrf_exempt 
def delete_files(request):
    file_list = json.loads(request.body)
    try:
        MQUtils.push_to_channel(MQChannels.FILE_TO_DELETE, {'files': file_list}, True)
        return JsonResponse({}, status=201)
    except:
        import traceback
        print(traceback.format_exc())
        return JsonResponse({}, status=500)

def add_download(request, folder_id):
    pass