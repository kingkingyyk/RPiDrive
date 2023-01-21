import http
import json
import os
import shutil

from datetime import (
    timezone as dt_tz,
    datetime,
    timedelta,
)
from typing import Any, ForwardRef, List, Optional
from uuid import UUID

from django.core.files.uploadedfile import (
    InMemoryUploadedFile,
    TemporaryUploadedFile,
)
from django.db import transaction
from django.db.models import Q, Value
from django.db.models.functions import Substr, Concat
from django.http.response import JsonResponse, HttpResponse
from django.utils import timezone
from django.views.decorators.http import (
    require_GET,
    require_POST,
    require_http_methods,
)
from pathvalidate import ValidationError, validate_filename
from pydantic import BaseModel

from drive.models import (
    FileObjectAlias,
    FileObjectTypeEnum,
    Job,
    LocalFileObject,
    StorageProvider,
    StorageProviderUser,
)
from drive.cache import ModelCache
from drive.core.local_file_object import move_file
from drive.core.local_file_object import serve, update_file_metadata
from drive.request_models import (
    MoveFileRequest,
    ZipFileRequest,
)
from drive.views.web.shared import (
    catch_error,
    generate_error_response,
    has_storage_provider_permission,
    login_required_401,
)
from drive.utils.indexer import Metadata

class ParentFileModel(BaseModel):
    """Parent File Model"""
    id: str
    name: str
    objType: str

class SPModel(BaseModel):
    """Storage Provider Model"""
    id: int
    name: str
    path: str

FileModel = ForwardRef('FileModel')
class FileModel(BaseModel):
    """File Model"""
    id: str
    name: str
    objType: str
    relPath: str
    extension: Optional[str]
    type: Optional[str]
    lastModified: datetime
    size: int
    parent: Optional[ParentFileModel]
    storageProvider: Optional[SPModel]
    metadata: Optional[Any]
    trace: Optional[List[ParentFileModel]]
    children: Optional[FileModel]
FileModel.update_forward_refs()

def has_permission(request, file: LocalFileObject):
    """Return user has permission on the file"""
    required_perms = {
        'GET': StorageProviderUser.PERMISSION.READ,
        'POST': StorageProviderUser.PERMISSION.READ_WRITE,
        'DELETE': StorageProviderUser.PERMISSION.READ_WRITE,
    }
    return has_storage_provider_permission(
        file.storage_provider, request.user,
        required_perms[request.method]
    )

def serialize_file_object(
    file: LocalFileObject,
    trace_parents=False,
    trace_children=False,
    trace_storage_provider=False,
    metadata=False
) -> FileModel:
    """Convert file object into dictionary"""
    data = FileModel(
        id=str(file.id),
        name=file.name,
        objType=file.obj_type,
        relPath=file.rel_path,
        extension=file.extension,
        type=file.type,
        lastModified=file.last_modified.astimezone(dt_tz.utc),
        size=file.size,
    )
    if file.parent:
        data.parent = ParentFileModel(
            id=str(file.parent.id),
            name=file.parent.name,
            objType=file.obj_type,
        )

    if trace_parents:
        parents = []
        while file.parent:
            parents.append(ParentFileModel(
                id=str(file.parent.id),
                name=file.parent.name,
                objType=file.obj_type
            ))
            file.parent = file.parent.parent
        parents.reverse()
        data.trace = parents
    if file.obj_type == FileObjectTypeEnum.FOLDER and trace_children:
        data.children = [
            serialize_file_object(
                x,
                trace_parents=False,
                trace_children=False,
                trace_storage_provider=False,
                metadata=False
            ) for x in file.children.all()
        ]

    if trace_storage_provider:
        data.storageProvider = SPModel( # pylint: disable=invalid-name
            id=str(file.storage_provider.pk),
            name=file.storage_provider.name,
            path=file.storage_provider.path
        )
    if metadata:
        update_file_metadata(file)
        data.metadata = file.metadata

    exclude_fields = set()
    if not trace_parents:
        exclude_fields.add('trace')
    if not trace_children:
        exclude_fields.add('children')
    if not trace_storage_provider:
        exclude_fields.add('storageProvider')
    if not metadata:
        exclude_fields.add('metadata')

    return data.dict(exclude=exclude_fields)

# pylint: disable=too-many-return-statements,too-many-branches
@login_required_401
@require_http_methods(['GET', 'POST', 'DELETE'])
@catch_error
def manage_file(request, file_id):
    """Handle get/update/delete of file"""
    if not LocalFileObject.objects.filter(id=file_id).exists():
        return generate_error_response(
            'Object not found', http.HTTPStatus.NOT_FOUND
        )

    file = LocalFileObject.objects.get(id=file_id)
    if not has_permission(request, file):
        return generate_error_response(
            'No permission to perform the operation!',
            http.HTTPStatus.FORBIDDEN,
        )

    if request.method == 'GET':
        action = request.GET.get('action', 'download')
        trace_parents = request.GET.get('traceParents', 'false') == 'true'
        trace_children = request.GET.get('traceChildren', 'false') == 'true'
        trace_storage_provider = request.GET.get('traceStorageProvider', 'false') == 'true'
        trace_metadata = request.GET.get('metadata', 'false') == 'true'
        if action == 'entity':
            data = serialize_file_object(
                file,
                trace_parents=trace_parents,
                trace_children=trace_children,
                trace_storage_provider=trace_storage_provider,
                metadata=trace_metadata
            )
            return JsonResponse(data)
        if action == 'metadata':
            return read_file_metadata(file)
        if action == 'album-image':
            return HttpResponse(
                Metadata.get_album_image(file),
                content_type='image/jpg'
            )
        if file.obj_type == FileObjectTypeEnum.FOLDER and action == 'children':
            return get_children(file)

        return generate_error_response(
            'Unknown action', http.HTTPStatus.BAD_REQUEST)

    if request.method == 'POST':
        action = request.GET.get('action', None)
        if action == 'new-files':
            return create_files(file, request)

        data = json.loads(request.body)
        if action == 'rename':
            return rename_file(file, data['name'])
        if action == 'new-folder':
            return create_new_folder(file, data['name'])

        return generate_error_response(
            'Unknown action', http.HTTPStatus.BAD_REQUEST)

    if request.method == 'DELETE':
        return delete_file(file)

    return generate_error_response(
        'Method not allowed', http.HTTPStatus.METHOD_NOT_ALLOWED)

@login_required_401
@require_POST
@catch_error
def move_files(request):
    """Handle file move action"""
    req_obj = MoveFileRequest.parse_obj(json.loads(request.body))

    # Verify destination exists
    dest_file_obj = LocalFileObject.objects.filter(id=req_obj.destination).first()
    if not dest_file_obj:
        return generate_error_response('Destination folder doesn\'t exist!')

    # Verify destination is folder
    if dest_file_obj.obj_type != FileObjectTypeEnum.FOLDER:
        return generate_error_response('Destination must be a folder!')

    # Check permission
    if not has_permission(request, dest_file_obj):
        return generate_error_response(
            'No permission to perform the operation!',
            http.HTTPStatus.FORBIDDEN,
        )
    storage_providers = (
        StorageProvider.objects.filter(
            pk__in=LocalFileObject.objects
                .filter(id__in=req_obj.files)
                .values_list('storage_provider__pk', flat=True)
                .distinct()
        ).all()
    )
    for s_p in storage_providers:
        if not has_storage_provider_permission(
            s_p, request.user,
            StorageProviderUser.PERMISSION.READ_WRITE
        ):
            return generate_error_response(
                'No permission to perform the operation!',
                http.HTTPStatus.FORBIDDEN,
            )

    # Enforce same storage provider
    if len(storage_providers) > 1:
        return generate_error_response(
            'Files must be under same storage provider!'
        )
    if storage_providers[0] != dest_file_obj.storage_provider:
        return generate_error_response(
            'Source & destination must have same storage provider!'
        )

    files_to_move = (
        LocalFileObject.objects
        .filter(id__in=req_obj.files)
        .all()
    )

    # Enforce same level items
    parent_count = (
        files_to_move
        .values_list('parent', flat=True)
        .distinct().count()
    )
    if parent_count != 1:
        return generate_error_response(
            'Only can move items in the same level!',
        )

    # Good to go
    failures = []
    for file in files_to_move:
        try:
            move_file(file, dest_file_obj, req_obj.strategy)
        except: # pylint: disable=bare-except
            failures.append(file.full_path)
    if failures:
        failures = '\n - '.join(failures)
        return generate_error_response(
            f'Failed to move:\n{failures}',
            http.HTTPStatus.INTERNAL_SERVER_ERROR,
        )

    return JsonResponse({})

@login_required_401
@require_POST
@catch_error
def zip_files(request):
    """Handle zip file action"""
    req_obj = ZipFileRequest.parse_obj(json.loads(request.body))

    # Verify destination exists
    dest_file_obj = LocalFileObject.objects.filter(id=req_obj.destination).first()
    if not dest_file_obj:
        return generate_error_response('Destination folder doesn\'t exist!')

    # Verify destination is folder
    if dest_file_obj.obj_type != FileObjectTypeEnum.FOLDER:
        return generate_error_response('Destination must be a folder!')

    # Check permission
    if not has_permission(request, dest_file_obj):
        return generate_error_response(
            'No permission to perform the operation!',
            http.HTTPStatus.FORBIDDEN,
        )
    storage_providers = (
        StorageProvider.objects.filter(
            pk__in=LocalFileObject.objects
                .filter(id__in=req_obj.files)
                .values_list('storage_provider__pk', flat=True)
                .distinct()
        ).all()
    )
    for s_p in storage_providers:
        if not has_storage_provider_permission(
            s_p, request.user,
            StorageProviderUser.PERMISSION.READ
        ):
            return generate_error_response(
                'No permission to perform the operation!',
                http.HTTPStatus.FORBIDDEN,
            )

    # Check file validity
    if not req_obj.filename or os.path.sep in req_obj.filename:
        return generate_error_response('Invalid name!')
    try:
        validate_filename(req_obj.filename)
    except ValidationError:
        return generate_error_response('Invalid name!')

    # Add .zip if not exists
    if not req_obj.filename.lower().endswith('.zip'):
        req_obj.filename = f'{req_obj.filename}.zip'

    # If exists zip file with same name
    zip_path = os.path.join(dest_file_obj.full_path, req_obj.filename)
    if os.path.exists(zip_path):
        return generate_error_response('Name is already used by another file.')

    Job.objects.create(
        task_type=Job.TaskTypes.ZIP,
        description=f'Creating zip file {dest_file_obj.full_path}/{req_obj.filename}',
        data=json.dumps(req_obj.dict()),
    )

    return JsonResponse({})

@login_required_401
@require_GET
@catch_error
def request_download_file(request, file_id):
    """Check user & serve file"""
    if not LocalFileObject.objects.filter(id=file_id).exists():
        return HttpResponse(status=http.HTTPStatus.NOT_FOUND)

    file = LocalFileObject.objects.get(id=file_id)
    if file.obj_type == FileObjectTypeEnum.FOLDER:
        return HttpResponse(status=http.HTTPStatus.NOT_FOUND)

    if not has_permission(request, file):
        return HttpResponse(status=http.HTTPStatus.FORBIDDEN)

    return serve_file(request, file)

@login_required_401
@require_POST
@catch_error
def generate_quick_access_link(request, file_id):
    """Generate quick access link"""
    file = LocalFileObject.objects.filter(id=file_id).first()

    if not file:
        return generate_error_response(
            'File not found!',
            http.HTTPStatus.NOT_FOUND,
        )

    if not has_permission(request, file):
        return generate_error_response(
            'No permission to create quick access link!',
            http.HTTPStatus.FORBIDDEN,
        )
    if file.obj_type == FileObjectTypeEnum.FOLDER:
        return generate_error_response(
            'Target file is a folder!',
            http.HTTPStatus.BAD_REQUEST
        )

    alias = FileObjectAlias.objects.create(
        local_ref=file,
        creator=request.user,
        expire_time=timezone.now() + timedelta(minutes=10),
    )

    return JsonResponse(data=dict(key=alias.id))

@require_GET
@catch_error
def request_quick_access_file(request):
    """Serve quick access file"""
    if 'key' not in request.GET:
        return HttpResponse(status=http.HTTPStatus.NOT_FOUND)

    key = request.GET['key']
    try:
        UUID(key, version=4)
    except ValueError:
        return HttpResponse(status=http.HTTPStatus.NOT_FOUND)

    alias = FileObjectAlias.objects.filter(id=key).first()

    if not alias:
        return HttpResponse(status=http.HTTPStatus.NOT_FOUND)
    if timezone.now() >= alias.expire_time:
        alias.delete()
        return HttpResponse(status=http.HTTPStatus.NOT_FOUND)

    return serve_file(request, alias.local_ref)

@login_required_401
@require_GET
@catch_error
def search_file(request):
    """Search file"""
    keyword = request.GET.get('keyword', None)
    if not keyword:
        return generate_error_response(
            'Keyword not found.'
        )
    result_files = (
        LocalFileObject.objects
        .filter(
            Q(name__search=keyword) | Q(name__icontains=keyword)
        )
        .order_by('-last_modified', 'name')
        .all()
    )
    result = []
    for file in result_files:
        if has_permission(request, file):
            result.append(
                serialize_file_object(file, trace_storage_provider=True)
            )
    return JsonResponse(dict(values=result))

def get_children(file: LocalFileObject):
    """Get file/folders in the folder"""
    if file.obj_type == FileObjectTypeEnum.FILE:
        return generate_error_response(
            'This action is only available for folders.',
        )
    values = [serialize_file_object(
        x) for x in file.children_set.all()]

    return JsonResponse(dict(values=values))

def rename_file(file, new_name):
    """Rename file"""
    # Same name, do nothing
    if new_name == file.name:
        return JsonResponse({})

    # Verify the filename is valid
    par_path = file.parent.full_path
    abs_path = os.path.abspath(os.path.join(par_path, new_name))
    if not abs_path.startswith(par_path) or len(abs_path) <= len(par_path):
        return generate_error_response('Invalid name!')
    try:
        validate_filename(new_name)
    except ValidationError:
        return generate_error_response('Invalid name!')

    # Verify siblings has different name than the target name
    sibling_names = LocalFileObject.objects.filter(
        parent__id=file.parent.id).values_list('name', flat=True)
    if new_name in sibling_names:
        return generate_error_response('Sibling already has same name!')

    # Good to go
    old_path = file.rel_path
    with transaction.atomic():
        parent_path = os.path.dirname(file.full_path)
        os.rename(file.full_path, os.path.join(parent_path, new_name))
        file = (
            LocalFileObject.objects
            .select_for_update(of=('self',)).get(id=file.id)
        )
        file.update_name(new_name)

        if file.obj_type == FileObjectTypeEnum.FOLDER:
            old_path += os.path.sep
            new_path = file.rel_path + os.path.sep
            LocalFileObject.objects.select_for_update(of=('self,')).filter(
                storage_provider__pk=file.storage_provider.pk,
                rel_path__startswith=old_path).update(
                    rel_path=Concat(Value(new_path), Substr('rel_path', len(old_path)+1)))

    return JsonResponse({})

def create_new_folder(file: LocalFileObject, folder_name: str):
    """Create new folder"""
    if file.obj_type != FileObjectTypeEnum.FOLDER:
        return generate_error_response('Only can create folder in a folder!')

    # Verify destination doesn't have file/folder with same name
    sibling_names = LocalFileObject.objects.filter(
        parent__id=file.id).values_list('name', flat=True)
    if folder_name in sibling_names:
        return generate_error_response('Sibling already has same name!')

    parent_path = file.full_path
    if parent_path.endswith(os.path.sep):
        parent_path = parent_path[:-1]
    f_p = os.path.abspath(os.path.join(parent_path, folder_name))
    if not f_p.startswith(parent_path+os.path.sep):
        return generate_error_response('Invalid name!')

    try:
        validate_filename(folder_name)
    except ValidationError:
        return generate_error_response('Invalid name!')

    with transaction.atomic():
        file = (
            LocalFileObject.objects
            .select_for_update(of=('self',)).get(pk=file.id)
        )
        os.mkdir(f_p)
        f_o = LocalFileObject(
            name=folder_name,
            obj_type=FileObjectTypeEnum.FOLDER,
            parent=file,
            storage_provider=file.storage_provider,
            rel_path=os.path.join(file.rel_path, folder_name),
            last_modified=datetime.fromtimestamp(
                os.path.getmtime(f_p), tz=timezone.get_current_timezone()),
            size=os.path.getsize(f_p),
        )
        f_o.save()

    return JsonResponse(
        serialize_file_object(f_o),
        status=http.HTTPStatus.CREATED
    )

def create_new_folder_safe(
    root_folder: LocalFileObject,
    rel_path: List[str]
) -> LocalFileObject:
    """Check and create folder on sanitized input"""
    curr_fp = root_folder.full_path
    for part in rel_path:
        curr_fp = os.path.join(curr_fp, part)
        if not os.path.exists(curr_fp):
            os.mkdir(curr_fp)
            root_folder = LocalFileObject(
                name=part,
                obj_type=FileObjectTypeEnum.FOLDER,
                parent=root_folder,
                storage_provider=root_folder.storage_provider,
                rel_path=os.path.join(root_folder.rel_path, part),
                last_modified=datetime.fromtimestamp(
                    os.path.getmtime(curr_fp),
                    tz=timezone.get_current_timezone()
                ),
                size=os.path.getsize(curr_fp),
            )
            root_folder.save()
        else:
            root_folder = LocalFileObject.objects.get(
                name=part,
                parent=root_folder,
            )
    return root_folder

def serve_file(request, file: LocalFileObject):
    """Serve file"""
    return serve(request, file.full_path)

def read_file_metadata(file: LocalFileObject):
    """Get file metadata"""
    update_file_metadata(file)
    return JsonResponse(file.metadata)

def create_files(file: LocalFileObject, request): # pylint: disable=too-many-locals
    """Handles incoming file"""
    file_form = 'files'
    if not request.FILES.get(file_form, None):
        return generate_error_response('No file was uploaded.')

    if file.obj_type != FileObjectTypeEnum.FOLDER:
        return generate_error_response('Destination must be a folder!')

    path_form = 'paths'

    with transaction.atomic():
        root_folder = (
            LocalFileObject.objects
            .select_for_update(of=('self',)).get(id=file.id)
        )
        file_list = request.FILES.getlist(file_form)
        path_list = request.POST.getlist(path_form)
        for idx, ul_file in enumerate(file_list):
            # Get file object & relative path
            ul_file = file_list[idx]
            rel_path_parts = path_list[idx].split('/')[:-1]

            ul_file_parent = create_new_folder_safe(root_folder, rel_path_parts)
            f_n = ul_file.name
            if os.path.exists(os.path.join(ul_file_parent.full_path, f_n)):
                counter = 1
                while True:
                    temp = f_n.split('.')
                    temp[-1 if len(temp) == 1 else -2] += f' ({counter})'
                    temp_fn = '.'.join(temp)
                    if not os.path.exists(os.path.join(ul_file_parent.full_path, temp_fn)):
                        f_n = temp_fn
                        break
                    counter += 1
            f_p = os.path.join(ul_file_parent.full_path, f_n)

            if isinstance(ul_file, InMemoryUploadedFile):
                with open(f_p, 'wb+') as f_h:
                    for chunk in ul_file.chunks():
                        f_h.write(chunk)
            elif isinstance(ul_file, TemporaryUploadedFile):
                shutil.move(ul_file.temporary_file_path(), f_p)
                os.chmod(f_p, 0o644)
            else:
                raise Exception(f'{ul_file} unknown upload handler.')

            f_o = LocalFileObject(
                name=f_n,
                obj_type=FileObjectTypeEnum.FILE,
                parent=ul_file_parent,
                storage_provider=ul_file_parent.storage_provider,
                rel_path=os.path.join(ul_file_parent.rel_path, f_n),
                last_modified=datetime.fromtimestamp(
                    os.path.getmtime(f_p), tz=timezone.get_current_timezone()),
                size=os.path.getsize(f_p),
            )
            f_o.save()

    return JsonResponse({}, status=http.HTTPStatus.CREATED)

def delete_file(file: LocalFileObject):
    """Delete file"""
    with transaction.atomic():
        if os.path.isfile(file.full_path):
            os.remove(file.full_path)
        elif os.path.isdir(file.full_path):
            shutil.rmtree(file.full_path)
        ModelCache.clear(file)
        LocalFileObject.objects.select_for_update(
            of=('self',)).get(id=file.id).delete()

    return JsonResponse({})
