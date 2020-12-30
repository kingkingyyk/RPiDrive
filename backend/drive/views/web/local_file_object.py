from django.http.response import JsonResponse, HttpResponse
from django.views.decorators.http import require_GET, require_POST, require_http_methods
from django.db import transaction
from django.views.static import serve
from drive.models import *
from django.conf import settings
from ...utils.indexer import Metadata
from .shared import generate_error_response
import json
import shutil


def serialize_file_object(file, trace_parents=False, metadata=False):
    data = {
        'id': file.id,
        'name': file.name,
        'objType': file.obj_type,
        'relPath': file.rel_path,
        'extension': file.extension,
        'type': file.type,
        'lastModified': file.last_modified,
        'size': file.size,
    }
    if file.parent:
        data['parent'] = {
            'id': file.parent.id,
            'name': file.parent.name
        }
    else:
        data['parent'] = None
    if trace_parents:
        parents = []
        while file.parent:
            parents.append({
                'id': file.parent.id,
                'name': file.parent.name
            })
            file.parent = file.parent.parent
        parents.reverse()
        data['trace'] = parents
    if metadata:
        data['metadata'] = read_file_metadata(file)
    return data


@require_http_methods(['GET', 'POST', 'DELETE'])
def manage_file(request, file_id):
    if not LocalFileObject.objects.filter(id=file_id).exists():
        return generate_error_response('Object not found', 404)

    file = LocalFileObject.objects.get(id=file_id)
    if request.method == 'GET':
        action = request.GET.get('action', 'download')
        if action == 'entity':
            return serialize_file_object(file, trace_parents=True)
        elif action == 'download':
            return serve_file(file, request)
        elif action == 'metadata':
            return read_file_metadata(file)
        elif action == 'children':
            return get_children(file)
        else:
            return generate_error_response('Unknown action', 400)
    elif request.method == 'POST':
        data = json.loads(request.body)
        action = request.GET.get('action', 'rename')
        if action == 'rename':
            return rename_file(file, data['name'])
        elif action == 'move':
            return move_file(file, data['destination'])
        elif action == 'new-folder':
            return create_new_folder(file, data['name'])
        elif action == 'new-files':
            return create_files(file, request)
        else:
            return generate_error_response('Unknown action', 400)
    elif request.method == 'DELETE':
        return delete_file(file)
    else:
        return generate_error_response('Method not allowed', 405)


def get_children(file):
    if file.obj_type == FileObjectType.FILE:
        return generate_error_response('This action is only available for folders.', 400)
    values = [serialize_file_object(
        x) for x in LocalFileObject.objects.filter(parent__id=file.id).all()]
    return JsonResponse({'values': values})


def rename_file(file, new_name):
    # Same name, do nothing
    if new_name == file.name:
        return JsonResponse({})

    # Verify siblings has different name than the target name
    sibling_names = [x for x in LocalFileObject.objects.filter(
        parent__id=file.parent.id).values_list('name', flat=True)]
    if new_name in sibling_names:
        return generate_error_response('Sibling already has same name!', 400)

    # Good to go
    with transaction.atomic():
        LocalFileObject.objects.select_for_update().get(id=file.id).update_name(new_name)
    return JsonResponse({})


def move_file(file, destination):
    # Verify folder exists
    if not LocalFileObject.objects.exists(id=destination):
        return generate_error_response('Destination folder doesn\'t exist!', 400)
    destination_file = LocalFileObject.objects.get(id=destination)

    # Verify destination is folder
    if destination_file.obj_type != FileObjectType.FOLDER:
        return generate_error_response('Destination must be a folder!', 400)

    # Verify destination doesn't have file/folder with same name
    filenames_in_destination = [x for x in LocalFileObject.objects.filter(
        parent__id=destination).values_list('name', flat=True)]
    if file.name in filenames_in_destination:
        return generate_error_response('Destination has the file/folder with same name!', 400)

    # Good to go
    with transaction.atomic():
        file = LocalFileObject.objects.select_for_update().get(id=file.id)
        destination_folder = LocalFileObject.objects.select_for_update().get(id=destination)
        shutil.move(file, destination_folder)
        file.rel_path = os.path.join(destination_folder.rel_path, file.name)
        file.save(update_fields=['rel_path'])
    return JsonResponse({})


def create_new_folder(file, folder_name):
    if file.obj_type != FileObjectType.FOLDER:
        return generate_error_response('Only can create folder in a folder!', 400)

    # Verify destination doesn't have file/folder with same name
    sibling_names = [x for x in LocalFileObject.objects.filter(
        parent__id=file.id).values_list('name', flat=True)]
    if folder_name in sibling_names:
        return generate_error_response('Sibling already has same name!', 400)

    fp = os.path.join(file.full_path, folder_name)

    with transaction.atomic():
        file = LocalFileObject.objects.select_for_update().get(id=file.id)
        os.mkdir(fp)
        fo = LocalFileObject(name=folder_name,
                             obj_type=FileObjectType.FOLDER,
                             parent=file,
                             storage_provider=file.storage_provider,
                             rel_path=os.path.join(file.rel_path, folder_name)
                             )
        fo.save()
    return JsonResponse(serialize_file_object(fo), status=201)


def serve_file(request, file):
    if settings.REVERSE_PROXY_TYPE == None:
        fp = file.full_path
        return serve(request, os.path.basename(fp), os.path.dirname(fp))
    elif settings.REVERSE_PROXY_TYPE == 'nginx':
        response = HttpResponse()
        response['X-Accel-Redirect'] = settings.REVERSE_PROXY_SERVE_FILE_URL + \
            '/' + file.rel_path
        return response
    elif settings.REVERSE_PROXY_TYPE == 'apache':
        response = HttpResponse()
        response['X-SendFile'] = settings.REVERSE_PROXY_SERVE_FILE_URL + \
            '/' + file.rel_path
        return response
    else:
        return generate_error_response('Reverse proxy server {} is not supported!'.format(settings.REVERSE_PROXY_TYPE), 500)


def read_file_metadata(file):
    if file.metadata is None:
        with transaction.atomic():
            LocalFileObject.objects.get(id=file.id).update(
                metadata=Metadata.extract(file))
    return JsonResponse(file.metadata)


def create_files(file, request):
    if file.obj_type != FileObjectType.FOLDER:
        return generate_error_response('Destination must be a folder!', 400)

    form = 'files'
    if request.FILES[form]:
        with transaction.atomic():
            file = LocalFileObject.objects.select_for_update().get(id=file.id)
            for temp_file in request.FILES.getlist(form):
                fn = temp_file.name
                if os.path.exists(os.path.join(file.full_path, fn)):
                    counter = 1
                    while True:
                        temp = fn.split('.')
                        if temp > 1:
                            temp[-2] = temp[-2] + '_' + str(counter)
                        else:
                            temp[-1] = temp[-1] + '_' + str(counter)
                        temp_fn = '.'.join(temp)
                        if not os.path.exists(os.path.join(file.full_path, temp_fn)):
                            fn = temp_fn
                            break
                        counter += 1
                fp = os.path.join(file.full_path, fn)
                shutil.move(temp_file.file, fp)
                fo = LocalFileObject(name=fn,
                                     obj_type=FileObjectType.FOLDER,
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
        LocalFileObject.objects.select_for_update().get(id=file.id).delete()
    return JsonResponse({}, status=200)
