import json
import os
import shutil
from datetime import timezone
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Value
from django.db.models.functions import Substr, Concat
from django.http.response import JsonResponse, HttpResponse
from django.views.decorators.http import require_GET, require_http_methods
from drive.models import (
    FileObjectType,
    LocalFileObject,
    StorageProviderUser,
)
from drive.cache import ModelCache
from drive.core.local_file_object import move_file
from drive.core.local_file_object import serve, update_file_metadata
from drive.views.web.shared import (
    generate_error_response,
    catch_error,
    has_storage_provider_permission
)
from drive.utils.indexer import Metadata


def get_file_stat(file):
    """Return cached file data"""
    if not ModelCache.exists(file):
        data = {
            'lastModified': file.last_modified.astimezone(timezone.utc),
            'size': file.size
        }
        ModelCache.set(file, data)
    return ModelCache.get(file)

def has_permission(request, file: LocalFileObject):
    """Return user has permission on the file"""
    required_perms = {
        'GET': StorageProviderUser.PERMISSION.READ,
        'POST': StorageProviderUser.PERMISSION.READ_WRITE,
        'DELETE': StorageProviderUser.PERMISSION.READ_WRITE,
    }
    return has_storage_provider_permission(
        file.storage_provider, request.user,
        required_perms[request.method])

def serialize_file_object(file: LocalFileObject,
                          trace_parents=False,
                          trace_children=False,
                          trace_storage_provider=False,
                          metadata=False):
    """Convert file object into dictionary"""
    file_stat = get_file_stat(file)
    data = {
        'id': file.id,
        'name': file.name,
        'objType': file.obj_type,
        'relPath': file.rel_path,
        'extension': file.extension,
        'type': file.type,
        'lastModified': file_stat['lastModified'],
        'size': file_stat['size'],
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


# pylint: disable=too-many-return-statements,too-many-branches
@login_required()
@require_http_methods(['GET', 'POST', 'DELETE'])
@catch_error
def manage_file(request, file_id):
    """Handle get/update/delete of file"""
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
        if action == 'metadata':
            return read_file_metadata(file)
        if action == 'album-image':
            return HttpResponse(Metadata.get_album_image(file),
                        content_type='image/jpg')
        if file.obj_type == FileObjectType.FOLDER and action == 'children':
            return get_children(file)

        return generate_error_response('Unknown action', 400)
    if request.method == 'POST':
        action = request.GET.get('action', 'rename')
        if action == 'new-files':
            return create_files(file, request)

        data = json.loads(request.body)
        if action == 'rename':
            return rename_file(file, data['name'])
        if action == 'move':
            return verify_and_move_file(file_id, data['destination'], data['strategy'])
        if action == 'new-folder':
            return create_new_folder(file, data['name'])

        return generate_error_response('Unknown action', 400)
    if request.method == 'DELETE':
        return delete_file(file)
    return generate_error_response('Method not allowed', 405)

@login_required()
@require_GET
@catch_error
def request_download_file(request, file_id):
    """Check user & serve file"""
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
    """Search file"""
    keyword = request.GET['keyword']
    result_files = LocalFileObject.objects.filter(name__search=keyword).all()
    result = []
    for file in result_files:
        if has_permission(request, file):
            result.append(serialize_file_object(file, trace_storage_provider=True))
    result = {'values': result}
    return JsonResponse(result)

def get_children(file):
    """Get file/folders in the folder"""
    if file.obj_type == FileObjectType.FILE:
        return generate_error_response('This action is only available for folders.', 400)
    values = [serialize_file_object(
        x) for x in file.children_set.all()]
    return JsonResponse({'values': values})


def rename_file(file, new_name):
    """Rename file"""
    # Same name, do nothing
    if new_name == file.name:
        return JsonResponse({})

    # Verify the filename is valid
    if os.path.sep in new_name:
        return generate_error_response('Invalid filename')

    # Verify siblings has different name than the target name
    sibling_names = LocalFileObject.objects.filter(
        parent__id=file.parent.id).values_list('name', flat=True)
    if new_name in sibling_names:
        return generate_error_response('Sibling already has same name!', 400)

    # Good to go
    old_path = file.rel_path
    with transaction.atomic():
        parent_path = os.path.dirname(file.full_path)
        os.rename(file.full_path, os.path.join(parent_path, new_name))
        file = LocalFileObject.objects.select_for_update(of=('self',)).get(id=file.id)
        file.update_name(new_name)

        if file.obj_type == FileObjectType.FOLDER:
            old_path += os.path.sep
            new_path = file.rel_path + os.path.sep
            print(old_path)
            print(new_path)
            LocalFileObject.objects.select_for_update(of=('self,')).filter(
                storage_provider__pk=file.storage_provider.pk,
                rel_path__startswith=old_path).update(
                    rel_path=Concat(Value(new_path), Substr('rel_path', len(old_path))))

    return JsonResponse({})


def verify_and_move_file(src_id, dest_id, strategy):
    """Move file"""
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
    """Create new folder"""
    if file.obj_type != FileObjectType.FOLDER:
        return generate_error_response('Only can create folder in a folder!', 400)

    # Verify destination doesn't have file/folder with same name
    sibling_names = LocalFileObject.objects.filter(
        parent__id=file.id).values_list('name', flat=True)
    if folder_name in sibling_names:
        return generate_error_response('Sibling already has same name!', 400)

    parent_path = file.full_path
    if parent_path.endswith(os.path.sep):
        parent_path = parent_path[:-1]
    f_p = os.path.abspath(os.path.join(parent_path, folder_name))

    if not f_p.startswith(parent_path+os.path.sep):
        return generate_error_response('Invalid name!', 400)

    with transaction.atomic():
        file = LocalFileObject.objects.select_for_update(of=('self',)).get(pk=file.id)
        os.mkdir(f_p)
        f_o = LocalFileObject(name=folder_name,
                              obj_type=FileObjectType.FOLDER,
                              parent=file,
                              storage_provider=file.storage_provider,
                              rel_path=os.path.join(file.rel_path, folder_name)
                              )
        f_o.save()
    return JsonResponse(serialize_file_object(f_o), status=201)


def serve_file(request, file: LocalFileObject):
    """Serve file"""
    return serve(request, file.full_path)

def read_file_metadata(file):
    """Get file metadata"""
    update_file_metadata(file)
    return JsonResponse(file.metadata)

def create_files(file, request):
    """Handles incoming file"""
    if file.obj_type != FileObjectType.FOLDER:
        return generate_error_response('Destination must be a folder!', 400)

    form = 'files'
    if request.FILES[form]:
        with transaction.atomic():
            file = LocalFileObject.objects.select_for_update(of=('self',)).get(id=file.id)
            for temp_file in request.FILES.getlist(form):
                f_n = temp_file.name
                if os.path.exists(os.path.join(file.full_path, f_n)):
                    counter = 1
                    while True:
                        temp = f_n.split('.')
                        temp[-1 if len(temp) == 1 else -2] += ' ({})'.format(str(counter))
                        temp_fn = '.'.join(temp)
                        if not os.path.exists(os.path.join(file.full_path, temp_fn)):
                            f_n = temp_fn
                            break
                        counter += 1
                f_p = os.path.join(file.full_path, f_n)
                with open(f_p, 'wb+') as f_h:
                    shutil.copyfileobj(temp_file.file, f_h, 10485760)
                f_o = LocalFileObject(name=f_n,
                                      obj_type=FileObjectType.FILE,
                                      parent=file,
                                      storage_provider=file.storage_provider,
                                      rel_path=os.path.join(file.rel_path, f_n)
                                      )
                f_o.save()
    return JsonResponse({}, status=201)


def delete_file(file):
    """Delete file"""
    with transaction.atomic():
        if os.path.isfile(file.full_path):
            os.remove(file.full_path)
        elif os.path.isdir(file.full_path):
            shutil.rmtree(file.full_path)
        ModelCache.clear(file)
        LocalFileObject.objects.select_for_update(of=('self',)).get(id=file.id).delete()
    return JsonResponse({}, status=200)
