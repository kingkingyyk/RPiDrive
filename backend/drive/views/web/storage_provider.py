import http
import json
import os

from typing import List, Optional

from django.db import transaction
from django.http.response import JsonResponse
from django.views.decorators.http import (
    require_GET,
    require_POST,
    require_http_methods,
)
from pydantic import BaseModel, Field

from drive.cache import ModelCache
from drive.core.storage_provider import create_storage_provider_helper
from drive.models import (
    Job,
    LocalFileObject,
    StorageProvider,
    StorageProviderTypeEnum,
    StorageProviderUser,
    User,
)
from drive.views.web.shared import (
    catch_error,
    generate_error_response,
    has_storage_provider_permission,
    login_required_401,
    requires_admin,
)

class StorageProviderCreationRequestModel(BaseModel):
    """Model for storage provider creation"""
    name: str = Field(..., min_length=1, max_length=50)
    type: StorageProviderTypeEnum
    path: str = Field(..., min_length=1)

    def validate_fields(self, exclude_paths=None):
        """Check the creation request data"""
        if not os.path.exists(self.path):
            raise Exception(f'Path {self.path} doesn\'t exist!')

        existing_paths = StorageProvider.objects.values_list('path', flat=True)
        if exclude_paths:
            existing_paths = [x for x in existing_paths if x not in exclude_paths]
        for path in existing_paths:
            if self.path == path:
                raise Exception('Path is already added.')
            if self.path.startswith(path):
                raise Exception(
                    f'Parent path {path} is already added, '
                    'so the files in this path already exist.'
                )
            if path.startswith(self.path):
                raise Exception(
                    f'Child path {path} is already added, '
                    'perhaps update existing provider instead?'
                )

class SPPermissionUserModel(BaseModel):
    """Model for StorageProvider user"""
    id: int
    username: Optional[str]

class SPPermissionModel(BaseModel):
    """Model for StorageProvider permission"""
    user: SPPermissionUserModel
    permission: int

class StorageProviderModel(BaseModel):
    """Model for StorageProvider serialization"""
    id: int
    name: str
    type: StorageProviderTypeEnum
    path: str
    rootFolder: str
    indexing: bool = False
    usedSpace: int = 0
    totalSpace: int = 0
    permissions: List[SPPermissionModel] = []

class UpdateSPPermissionModel(BaseModel):
    """Model for updating StorageProvider permission"""
    permissions: List[SPPermissionModel]

def serialize_storage_provider(
    s_p: StorageProvider,
    disk_space=False, permission=False,
    refresh_cache=False,
):
    """Convert storage provider into dictionary"""
    if not ModelCache.exists(s_p) or refresh_cache:
        root_folder = (
            LocalFileObject.objects
            .select_related('parent', 'storage_provider')
            .filter(storage_provider__pk=s_p.pk, parent=None)
            .first()
        )

        ModelCache.set(
            s_p,
            StorageProviderModel(
                id=s_p.pk,
                name=s_p.name,
                type=s_p.type,
                path=s_p.path,
                rootFolder=str(root_folder.pk),
            ).dict()
        )

    data = StorageProviderModel.parse_obj(ModelCache.get(s_p))
    data.indexing = s_p.indexing

    if disk_space:
        data.usedSpace = s_p.used_space
        data.totalSpace = s_p.total_space

    if permission:
        data.permissions = [
            SPPermissionModel(
                user=SPPermissionUserModel(
                    id=x.user.pk,
                    username=x.user.username,
                ),
                permission=x.permission
            )
            for x in s_p.storageprovideruser_set.all()
        ]

    return data.dict()

# Don't need to login, used by setup page.
@require_GET
def get_storage_provider_types(request):
    """Return types of storage provider available"""
    data = [
        dict(
            name=x[0],
            value=x[1],
         ) for x in StorageProviderTypeEnum.pairs()
    ]
    return JsonResponse(dict(values=data))

@login_required_401
@require_GET
@catch_error
def get_storage_providers(request):
    """Return storage providers viewable by user"""
    data = []
    for s_p in StorageProvider.objects.prefetch_related(
            'storageprovideruser_set').order_by('pk').all():
        if has_storage_provider_permission(
            s_p, request.user,
            StorageProviderUser.PERMISSION.READ
        ):
            data.append(serialize_storage_provider(
                s_p, disk_space=True
            ))
    return JsonResponse(dict(values=data))

@login_required_401
@require_POST
@requires_admin
@catch_error
def create_storage_provider(request):
    """Create storage provider"""
    data = StorageProviderCreationRequestModel.parse_obj(
        json.loads(request.body)
    )
    data.path = os.path.abspath(data.path)

    try:
        data.validate_fields()
    except Exception as e: # pylint: disable=broad-except, invalid-name
        return generate_error_response(str(e))

    # Validate name
    used_names = set(StorageProvider.objects.values_list('name', flat=True))
    if data.name in used_names:
        return generate_error_response('Name is already in use!')

    with transaction.atomic():
        # pylint: disable=unused-variable
        s_p, _ = create_storage_provider_helper(
            name=data.name,
            sp_type=data.type,
            path=data.path,
        )
    return JsonResponse(
        serialize_storage_provider(s_p, True),
        status=http.HTTPStatus.CREATED
    )

# pylint: disable=too-many-return-statements, too-many-branches
@login_required_401
@require_http_methods(['GET', 'POST', 'DELETE'])
#@catch_error
def manage_storage_provider(request, provider_id):
    """Get/update/delete storage provider"""
    s_p = StorageProvider.objects.filter(pk=provider_id).first()
    if not s_p:
        return generate_error_response(
            'Storage provider not found.',
            status=http.HTTPStatus.NOT_FOUND,
        )

    required_levels = {
        'GET': StorageProviderUser.PERMISSION.READ,
        'POST': StorageProviderUser.PERMISSION.ADMIN,
        'DELETE': StorageProviderUser.PERMISSION.ADMIN
    }
    if not has_storage_provider_permission(
        s_p, request.user, required_levels[request.method]
    ):
        return generate_error_response(
            'No permission to perform the operation.',
            status=http.HTTPStatus.FORBIDDEN,
        )

    if request.method == 'GET':
        query_perm = request.GET.get('permissions', 'true') == 'true'
        if query_perm and not has_storage_provider_permission(
            s_p, request.user, StorageProviderUser.PERMISSION.ADMIN
        ):
            return generate_error_response(
                'No permission to access the resource.',
                status=http.HTTPStatus.FORBIDDEN,
            )
        return JsonResponse(
            serialize_storage_provider(s_p, permission=query_perm)
        )

    if request.method == 'POST':
        action = request.GET.get('action')
        if action not in ('basic', 'permissions'):
            return generate_error_response('Invalid action!')

        with transaction.atomic():
            if action == 'basic':
                data = StorageProviderCreationRequestModel.parse_obj(
                    json.loads(request.body)
                )
                data.validate_fields(exclude_paths={s_p.path})
                do_index = data.path != s_p.path

                s_p.name = data.name
                s_p.type = data.type
                s_p.path = data.path
                s_p.save()

                if do_index:
                    create_index_job(s_p)
            elif action == 'permissions':
                data = UpdateSPPermissionModel.parse_obj(
                    json.loads(request.body)
                )

                perms = []
                user_pks = User.objects.all().values_list('pk', flat=True)
                for perm in data.permissions:
                    if perm.permission not in StorageProviderUser.PERMISSIONS:
                        return generate_error_response('Invalid permission type!')
                    if perm.user.id not in user_pks:
                        return generate_error_response('User not found!')
                    perms.append(
                        StorageProviderUser(
                            storage_provider=s_p,
                            permission=perm.permission,
                            user_id=perm.user.id
                        )
                    )

                StorageProviderUser.objects.filter(
                    storage_provider=s_p).delete()
                StorageProviderUser.objects.bulk_create(perms)
                s_p.refresh_from_db()

        return JsonResponse(serialize_storage_provider(
            s_p, True, permission=True, refresh_cache=True
        ))

    if request.method == 'DELETE':
        ModelCache.clear(s_p)
        s_p.delete()
        return JsonResponse({})

    return JsonResponse({}, status=http.HTTPStatus.METHOD_NOT_ALLOWED)

@login_required_401
@require_GET
@catch_error
def get_storage_provider_permissions(request):
    """Get storage provider permissions"""
    return JsonResponse(
        dict(
            values=[
                dict(
                    name=x[1],
                    value=x[0],
                )
                for x in StorageProviderUser.PERMISSION_CHOICES
            ]
        )
    )

@login_required_401
@require_POST
@catch_error
def perform_index(request, provider_id):
    """Perform index on storage provider"""
    strg_provider = StorageProvider.objects.filter(pk=provider_id).first()
    if not strg_provider:
        return generate_error_response(
            'Provider not found!',
            status=http.HTTPStatus.NOT_FOUND,
        )


    if not has_storage_provider_permission(
        strg_provider,
        request.user,
        StorageProviderUser.PERMISSION.READ_WRITE,
    ):
        return generate_error_response(
            'No permission to perform the operation.',
            status=http.HTTPStatus.FORBIDDEN,
        )

    if not strg_provider.indexing:
        create_index_job(strg_provider)
    return JsonResponse({})

def create_index_job(s_p: StorageProvider):
    """Create index job for storage provider"""
    s_p.indexing = True
    s_p.save(update_fields=['indexing'])

    Job.objects.create(
        task_type=Job.TaskTypes.INDEX,
        description=f'Perform indexing on {s_p.path}',
        data=s_p.pk,
    )
