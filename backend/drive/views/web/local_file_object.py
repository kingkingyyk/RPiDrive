import json
import shutil
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db import transaction
from django.http.response import JsonResponse, HttpResponse
from django.views.decorators.http import require_GET, require_POST, require_http_methods
from drive.models import *
from datetime import timezone
from ...core.local_file_object import move_file
from ...core.local_file_object import serve, update_file_metadata
from .shared import generate_error_response, catch_error, has_storage_provider_permission
from ...utils.indexer import Metadata
from django.core.cache import cache

# ========================= CACHE ============================
def get_file_cache_key(pk: str):
    return 'file-{}'.format(pk)


def get_cached_file_data(file):
    cache_key = get_file_cache_key(file.pk)+'-data'
    if not cache.has_key(cache_key):
        data = {
            'lastModified': file.last_modified.astimezone(timezone.utc),
            'size': file.size
        }
        cache.set(cache_key, data)
    return cache.get(cache_key)


def clear_file_cache(pk: str):
    cache.delete(get_file_cache_key(pk)+'-last_modified')
    cache.delete(get_file_cache_key(pk)+'-size')

# ========================= CACHE ============================
def has_permission(request, file: LocalFileObject):
    required_perms = {
        'GET': StorageProviderUser.PERMISSION.READ,
        'POST': StorageProviderUser.PERMISSION.READ_WRITE,
        'DELETE': StorageProviderUser.PERMISSION.READ_WRITE,
    }
    return has_storage_provider_permission(
        file.storage_provider, request.user,
        required_perms[request.method])

# ========================= OPERATIONS ============================

def serialize_file_object(file: LocalFileObject,
                          trace_parents=False,
                          trace_children=False,
                          trace_storage_provider=False,
                          metadata=False):
    data = {
        'id': file.id,
        'name': file.name,
        'objType': file.obj_type,
        'relPath': file.rel_path,
        'extension': file.extension,
        'type': file.type,
        'lastModified': get_cached_file_data(file)['lastModified'],
        'size': get_cached_file_data(file)['size'],
    }
    if file.parent:
        data['parent'] = {
            'id': file.parent.id,
            'name': file.parent.name,
            'objType': file.obj_type
        }
    else:
        data['parent'] = None

    if trace_parents:
        parents = []
        while file.parent:
            parents.append({
                'id': file.parent.id,
                'name': file.parent.name,
                'objType': file.obj_type
            })
            file.parent = file.parent.parent
        parents.reverse()
        data['trace'] = parents
    if file.obj_type == FileObjectType.FOLDER and trace_children:
        data['children'] = [
            serialize_file_object(x,trace_parents=False,
                                  trace_children=False,
                                  trace_storage_provider=False,
                                  metadata=False)
            for x in file.children.all()
        ]
    if trace_storage_provider:
        data['storageProvider']= {
            'id': file.storage_provider.pk,
            'name': file.storage_provider.name,
            'path': file.storage_provider.path
        }
    if metadata:
        update_file_metadata(file)
        data['metadata'] = file.metadata
    return data


@login_required()
@require_http_methods(['GET', 'POST', 'DELETE'])
@catch_error
def manage_file(request, file_id):
    if not LocalFileObject.objects.filter(id=file_id).exists():
        return generate_error_response('Object not found', 404)

    file = LocalFileObject.objects.get(id=file_id)
    if not has_permission(request, file):
        return generate_error_response('No permission to perform the operation!',
                                        403)

    if request.method == 'GET':
        action = request.GET.get('action', 'download')
        trace_parents = request.GET.get('traceParents', 'false') == 'true'
        trace_children = request.GET.get('traceChildren', 'false') == 'true'
        trace_storage_provider = request.GET.get('traceStorageProvider', 'false') == 'true'
        trace_metadata = request.GET.get('metadata', 'false') == 'true'
        if action == 'entity':
            data = serialize_file_object(file, 
                                         trace_parents=trace_parents,
                                         trace_children=trace_children,
                                         trace_storage_provider=trace_storage_provider,
                                         metadata=trace_metadata)
            return JsonResponse(data)
        elif action == 'metadata':
            return read_file_metadata(file)
        elif action == 'album-image':
            return HttpResponse(Metadata.get_album_image(file),
                        content_type='image/jpg')
        elif file.obj_type == FileObjectType.FOLDER and action == 'children':
            return get_children(file)
        else:
            return generate_error_response('Unknown action', 400)
    elif request.method == 'POST':
        action = request.GET.get('action', 'rename')
        if action == 'new-files':
            return create_files(file, request)

        data = json.loads(request.body)
        if action == 'rename':
            return rename_file(file, data['name'])
        elif action == 'move':
            return verify_and_move_file(file_id, data['destination'], data['strategy'])
        elif action == 'new-folder':
            return create_new_folder(file, data['name'])
        else:
            return generate_error_response('Unknown action', 400)
    elif request.method == 'DELETE':
        return delete_file(file)
    else:
        return generate_error_response('Method not allowed', 405)

@login_required()
@require_GET
@catch_error
def request_download_file(request, file_id):
    if not LocalFileObject.objects.filter(id=file_id).exists():
        return generate_error_response('Object not found', 404)

    file = LocalFileObject.objects.get(id=file_id)
    if not has_permission(request, file):
        return generate_error_response('No permission to access this resource.',
                                       403)
    if file.obj_type == FileObjectType.FOLDER:
        return HttpResponse(None, status=404)

    return serve_file(request, file)

@login_required()
@require_GET
@catch_error
def search_file(request):
    keyword = request.GET['keyword']
    result_files = LocalFileObject.objects.filter(name__search=keyword).all()
    result = []
    for file in result_files:
        if has_permission(request, file):
            result.append(serialize_file_object(x, trace_storage_provider=True))
    result = {'values': result}
    return JsonResponse(result)
    
def get_children(file):
    if file.obj_type == FileObjectType.FILE:
        return generate_error_response('This action is only available for folders.', 400)
    values = [serialize_file_object(
        x) for x in file.children_set.all()]
    return JsonResponse({'values': values})


def rename_file(file, new_name):
    # Same name, do nothing
    if new_name == file.name:
        return JsonResponse({})

    # Verify the filename is valid
    if os.path.sep in new_name:
        return generate_error_response('Invalid filename')

    # Verify siblings has different name than the target name
    sibling_names = [x for x in LocalFileObject.objects.filter(
        parent__id=file.parent.id).values_list('name', flat=True)]
    if new_name in sibling_names:
        return generate_error_response('Sibling already has same name!', 400)

    # Good to go
    with transaction.atomic():
        parent_path = os.path.dirname(file.full_path)
        os.rename(file.full_path, os.path.join(parent_path, new_name))
        LocalFileObject.objects.select_for_update(of=('self',)).get(id=file.id).update_name(new_name)

    return JsonResponse({})


def verify_and_move_file(src_id, dest_id, strategy):
    # Verify folder exists
    dest_file_obj = LocalFileObject.objects.filter(id=dest_id).first()
    if not dest_file_obj:
        return generate_error_response('Destination folder doesn\'t exist!', 400)

    # Verify destination is folder
    if dest_file_obj.obj_type != FileObjectType.FOLDER:
        return generate_error_response('Destination must be a folder!', 400)

    # Good to go
    with transaction.atomic():
        src = LocalFileObject.objects.select_for_update(of=('self',)).get(id=src_id)
        dest = LocalFileObject.objects.select_for_update(of=('self',)).get(id=dest_id)
        move_file(src, dest, strategy)

    return JsonResponse({})


def create_new_folder(file, folder_name):
    if file.obj_type != FileObjectType.FOLDER:
        return generate_error_response('Only can create folder in a folder!', 400)

    # Verify destination doesn't have file/folder with same name
    sibling_names = [x for x in LocalFileObject.objects.filter(
        parent__id=file.id).values_list('name', flat=True)]
    if folder_name in sibling_names:
        return generate_error_response('Sibling already has same name!', 400)

    parent_path = file.full_path
    if parent_path.endswith(os.path.sep):
        parent_path = parent_path[:-1]
    fp = os.path.abspath(os.path.join(parent_path, folder_name))

    if not fp.startswith(parent_path+os.path.sep):
        return generate_error_response('Invalid name!', 400)

    with transaction.atomic():
        file = LocalFileObject.objects.select_for_update(of=('self',)).get(pk=file.id)
        os.mkdir(fp)
        fo = LocalFileObject(name=folder_name,
                             obj_type=FileObjectType.FOLDER,
                             parent=file,
                             storage_provider=file.storage_provider,
                             rel_path=os.path.join(file.rel_path, folder_name)
                             )
        fo.save()
    return JsonResponse(serialize_file_object(fo), status=201)


def serve_file(request, file: LocalFileObject):
    fp = file.full_path
    return serve(request, fp)

def read_file_metadata(file):
    update_file_metadata(file)
    return JsonResponse(file.metadata)

def create_files(file, request):
    if file.obj_type != FileObjectType.FOLDER:
        return generate_error_response('Destination must be a folder!', 400)

    form = 'files'
    if request.FILES[form]:
        with transaction.atomic():
            file = LocalFileObject.objects.select_for_update(of=('self',)).get(id=file.id)
            for temp_file in request.FILES.getlist(form):
                fn = temp_file.name
                if os.path.exists(os.path.join(file.full_path, fn)):
                    counter = 1
                    while True:
                        temp = fn.split('.')
                        temp[-1 if len(temp) == 1 else -2] += ' ({})'.format(str(counter))
                        temp_fn = '.'.join(temp)
                        if not os.path.exists(os.path.join(file.full_path, temp_fn)):
                            fn = temp_fn
                            break
                        counter += 1
                fp = os.path.join(file.full_path, fn)
                with open(fp, 'wb+') as f:
                    shutil.copyfileobj(temp_file.file, f, 10485760)
                fo = LocalFileObject(name=fn,
                                     obj_type=FileObjectType.FILE,
                                     parent=file,
                                     storage_provider=file.storage_provider,
                                     rel_path=os.path.join(file.rel_path, fn)
                                     )
                fo.save()
    return JsonResponse({}, status=201)


def delete_file(file):
    with transaction.atomic():
        if os.path.isfile(file.full_path):
            os.remove(file.full_path)
        elif os.path.isdir(file.full_path):
            shutil.rmtree(file.full_path)
        LocalFileObject.objects.select_for_update(of=('self',)).get(id=file.id).delete()
        clear_file_cache(id)
    return JsonResponse({}, status=200)
