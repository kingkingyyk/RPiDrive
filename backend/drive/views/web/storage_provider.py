import json
import os
from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.db import transaction
from django.http.response import JsonResponse
from django.views.decorators.http import require_GET, require_POST, require_http_methods
from drive.core.storage_provider import create_storage_provider_helper
from drive.models import (
    LocalFileObject,
    StorageProvider,
    StorageProviderType,
    StorageProviderUser,
    User,
)
#from drive.views.web.local_file_object import *
from drive.views.web.shared import (
    catch_error,
    generate_error_response,
    has_storage_provider_permission,
    requires_admin,
)
from drive.utils.indexer import LocalStorageProviderIndexer


class StorageProviderRequest:
    """StorageProvider request keys"""
    ID_KEY = 'id'
    NAME_KEY = 'name'
    TYPE_KEY = 'type'
    PATH_KEY = 'path'
    USED_SPACE_KEY = 'usedSpace'
    TOTAL_SPACE_KEY = 'totalSpace'
    INDEXING_KEY = 'indexing'
    ROOT_FOLDER_KEY = 'rootFolder'
    PERMISSION_KEY = 'permissions'

    @staticmethod
    def _inspect_type(sp_type):
        if sp_type not in StorageProviderType.VALUES:
            raise Exception('The provider type is incorrect! Supported types are {}!'.format(
                ', '.join(StorageProviderType.VALUES)))

    @staticmethod
    def inspect_create_data(data):
        """Check the creation request data"""
        needed_keys = [StorageProviderRequest.NAME_KEY,
                       StorageProviderRequest.TYPE_KEY,
                       StorageProviderRequest.PATH_KEY]
        missing = [x for x in needed_keys if x not in data.keys()]
        if missing:
            raise Exception(
                'The following fields ({}) are missing!'.format(', '.join(missing)))
        StorageProviderRequest._inspect_type(
            data[StorageProviderRequest.TYPE_KEY])

        if not os.path.exists(data[StorageProviderRequest.PATH_KEY]):
            raise Exception('Path {} doesn\'t exist!'.format(
                data[StorageProviderRequest.PATH_KEY]))


def get_storage_provider_cache_key(p_k: int):
    """Return cache key for storage provider"""
    return 'storage-provider-{}'.format(p_k)


def serialize_storage_provider(
    request, s_p, disk_space=False, permission=False,
    refresh_cache=False):
    """Convert storage provider into dictionary"""
    cache_key = get_storage_provider_cache_key(s_p)

    if not cache.has_key(cache_key) or refresh_cache:
        root_folder = LocalFileObject.objects\
            .select_related('parent', 'storage_provider')\
            .filter(storage_provider__pk=s_p.pk, parent=None)\
            .first()

        data = {
            StorageProviderRequest.ID_KEY: s_p.pk,
            StorageProviderRequest.NAME_KEY: s_p.name,
            StorageProviderRequest.TYPE_KEY: s_p.type,
            StorageProviderRequest.PATH_KEY: s_p.path,
            StorageProviderRequest.ROOT_FOLDER_KEY: root_folder.pk,
        }
        cache.set(cache_key, data)

    data = cache.get(cache_key)
    data[StorageProviderRequest.INDEXING_KEY] = s_p.indexing

    if disk_space:
        data[StorageProviderRequest.USED_SPACE_KEY] = s_p.used_space
        data[StorageProviderRequest.TOTAL_SPACE_KEY] = s_p.total_space

    if permission:
        data[StorageProviderRequest.PERMISSION_KEY] = [
            {
                'user': {
                    'id': x.user.pk,
                    'username': x.user.username
                },
                'permission': x.permission
            }
            for x in s_p.storageprovideruser_set.all()
        ]

    return data

# Don't need to login, used by setup page.
@require_GET
@catch_error
def get_storage_provider_types(request):
    """Return types of storage provider available"""
    data = [
        {
            'name': x[0],
            'value': x[1],
        } for x in StorageProviderType.TYPES
    ]
    return JsonResponse({'values': data})


@login_required()
@require_GET
@catch_error
def get_storage_providers(request):
    """Return storage providers viewable by user"""
    data = []
    for s_p in StorageProvider.objects.prefetch_related(
        'storageprovideruser_set').all():
        if has_storage_provider_permission(s_p, request.user, StorageProviderUser.PERMISSION.READ):
            data.append(serialize_storage_provider(request, s_p, disk_space=True))
    return JsonResponse({'values': data})


@login_required()
@require_POST
@catch_error
@requires_admin
def create_storage_provider(request):
    """Create storage provider"""
    data = json.loads(request.body)

    try:
        StorageProviderRequest.inspect_create_data(data)
    except Exception as e: # pylint: disable=broad-except, invalid-name
        return generate_error_response(str(e))

    with transaction.atomic():
        # pylint: disable=unused-variable
        s_p, root_fo = create_storage_provider_helper(
            name=data[StorageProviderRequest.NAME_KEY],
            sp_type=data[StorageProviderRequest.TYPE_KEY],
            path=data[StorageProviderRequest.PATH_KEY])
    return JsonResponse(serialize_storage_provider(request, s_p, True))


# pylint: disable=too-many-return-statements, too-many-branches
@login_required()
@require_http_methods(['GET', 'POST', 'DELETE'])
@catch_error
def manage_storage_provider(request, provider_id):
    """Get/update/delete storage provider"""
    try:
        s_p = StorageProvider.objects.get(pk=provider_id)
    except: # pylint: disable=broad-except, raise-missing-from
        raise Exception('Provider not found!')

    required_levels = {
        'GET': StorageProviderUser.PERMISSION.READ,
        'POST': StorageProviderUser.PERMISSION.ADMIN,
        'DELETE': StorageProviderUser.PERMISSION.ADMIN
    }
    if not has_storage_provider_permission(s_p, request.user, required_levels[request.method]):
        return generate_error_response('No permission to perform the operation.',
                                        status=403)

    if request.method == 'GET':
        query_perm = bool(request.GET.get('permissions', 'true'))
        if query_perm and not request.user.is_superuser:
            return generate_error_response('No permission to access the resource.',
                                            status=403)
        return JsonResponse(serialize_storage_provider(request, s_p, permission=True))
    if request.method == 'POST':
        data = json.loads(request.body)
        action = request.GET.get('action')
        if action not in ('basic', 'permissions'):
            return generate_error_response('Bad request')

        with transaction.atomic():
            if action == 'basic':
                s_p.name = data[StorageProviderRequest.NAME_KEY]

                old_path = s_p.path
                if not os.path.exists(data[StorageProviderRequest.PATH_KEY]):
                    return generate_error_response('Path doesn\'t exist!')
                s_p.path = data[StorageProviderRequest.PATH_KEY]

                s_p.save()

                if s_p.path != old_path:
                    perform_index(request, s_p.pk)
            elif action == 'permissions':
                StorageProviderUser.objects.filter(
                    storage_provider=s_p).delete()

                perms = []
                user_pks = User.objects.all().values_list('pk', flat=True)
                for perm in data[StorageProviderRequest.PERMISSION_KEY]:
                    if perm['permission'] not in StorageProviderUser.PERMISSIONS:
                        raise Exception('Invalid permission type!')
                    if perm['user']['id'] not in user_pks:
                        raise Exception('User not found!')
                    perms.append(StorageProviderUser(
                        storage_provider=s_p, permission=perm['permission'],
                        user_id=perm['user']['id']))
                StorageProviderUser.objects.bulk_create(perms)

        return JsonResponse(serialize_storage_provider(request, s_p, True, refresh_cache=True))
    if request.method == 'DELETE':
        s_p.delete()
        cache.delete(s_p.pk)
        return JsonResponse({})
    return JsonResponse({}, status=405)

@login_required()
@require_GET
@catch_error
def get_storage_provider_permissions(request):
    """Get storage provider permissions"""
    values = [
        {'name': x[1], 'value': x[0]}
        for x in StorageProviderUser.PERMISSION_CHOICES
    ]
    return JsonResponse({'values': values})


@login_required()
@require_POST
@catch_error
def perform_index(request, provider_id):
    """Perform index on storage provider"""
    try:
        s_p = StorageProvider.objects.get(pk=provider_id)
    except: # pylint: disable=broad-except, raise-missing-from
        raise Exception('Provider not found!')

    if not has_storage_provider_permission(
        s_p, request.user, StorageProviderUser.PERMISSION.READ_WRITE):
        return generate_error_response(
            'No permission to perform the operation.', status=403)

    s_p.indexing = True
    s_p.save(update_fields=['indexing'])
    return JsonResponse({})
