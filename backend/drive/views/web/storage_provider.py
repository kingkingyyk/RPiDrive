from django.contrib.auth.decorators import login_required
from django.http.response import JsonResponse
from django.views.decorators.http import require_GET, require_POST, require_http_methods
from django.db.models import Prefetch
from drive.models import *
from .local_file_object import *
from ...utils.indexer import LocalStorageProviderIndexer
from ...core.storage_provider import create_storage_provider_helper
from .shared import generate_error_response, has_storage_provider_permission, requires_admin
from django.core.cache import cache
import json
import os


class StorageProviderRequest:
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
        NEEDED_KEYS = [StorageProviderRequest.NAME_KEY,
                       StorageProviderRequest.TYPE_KEY,
                       StorageProviderRequest.PATH_KEY]
        missing = [x for x in NEEDED_KEYS if x not in data.keys()]
        if missing:
            raise Exception(
                'The following fields ({}) are missing!'.format(', '.join(missing)))
        StorageProviderRequest._inspect_type(
            data[StorageProviderRequest.TYPE_KEY])

        if not os.path.exists(data[StorageProviderRequest.PATH_KEY]):
            raise Exception('Path {} doesn\'t exist!'.format(
                data[StorageProviderRequest.PATH_KEY]))


def get_storage_provider_cache_key(pk: int):
    return 'storage-provider-{}'.format(pk)


def serialize_storage_provider(
    request, sp, disk_space=False, permission=False,
    refresh_cache=False):
    cache_key = get_storage_provider_cache_key(sp)

    if not cache.has_key(cache_key) or refresh_cache:
        root_folder = LocalFileObject.objects\
            .select_related('parent', 'storage_provider')\
            .filter(storage_provider__pk=sp.pk, parent=None)\
            .first()

        data = {
            StorageProviderRequest.ID_KEY: sp.pk,
            StorageProviderRequest.NAME_KEY: sp.name,
            StorageProviderRequest.TYPE_KEY: sp.type,
            StorageProviderRequest.PATH_KEY: sp.path,
            StorageProviderRequest.ROOT_FOLDER_KEY: root_folder.pk,
        }
        cache.set(cache_key, data)

    data = cache.get(cache_key)
    data[StorageProviderRequest.INDEXING_KEY] = sp.indexing
    
    if disk_space:
        data[StorageProviderRequest.USED_SPACE_KEY] = sp.used_space
        data[StorageProviderRequest.TOTAL_SPACE_KEY] = sp.total_space

    if permission:
        data[StorageProviderRequest.PERMISSION_KEY] = [
            {
                'user': {
                    'id': x.user.pk,
                    'username': x.user.username
                },
                'permission': x.permission
            } 
            for x in sp.storageprovideruser_set.all()
        ]
        
    return data

# Don't need to login, used by setup page.
@require_GET
@catch_error
def get_storage_provider_types(request):
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
    data = []
    for x in StorageProvider.objects.prefetch_related(
        'storageprovideruser_set').all():
        if has_storage_provider_permission(x, request.user, StorageProviderUser.PERMISSION.READ):
            data.append(serialize_storage_provider(request, x, disk_space=True))
    return JsonResponse({'values': data})


@login_required()
@require_POST
@catch_error
@requires_admin
def create_storage_provider(request):
    data = json.loads(request.body)

    try:
        StorageProviderRequest.inspect_create_data(data)
    except Exception as e:
        return generate_error_response(str(e))

    with transaction.atomic():
        sp, root_fo = create_storage_provider_helper(name=data[StorageProviderRequest.NAME_KEY],
                                            type=data[StorageProviderRequest.TYPE_KEY],
                                            path=data[StorageProviderRequest.PATH_KEY])
    return JsonResponse(serialize_storage_provider(request, sp, True))


@login_required()
@require_http_methods(['GET', 'POST', 'DELETE'])
@catch_error
def manage_storage_provider(request, provider_id):
    try:
        sp = StorageProvider.objects.get(pk=provider_id)
    except:
        raise Exception('Provider not found!')

    required_levels = {
        'GET': StorageProviderUser.PERMISSION.READ,
        'POST': StorageProviderUser.PERMISSION.ADMIN,
        'DELETE': StorageProviderUser.PERMISSION.ADMIN
    }
    if not has_storage_provider_permission(sp, request.user, required_levels[request.method]):
        return generate_error_response('No permission to perform the operation.',
                                        status=403)

    if request.method == 'GET':
        query_perm = bool(request.GET.get('permissions', 'true'))
        if query_perm and not request.user.is_superuser:
            return generate_error_response('No permission to access the resource.',
                                            status=403)
        return JsonResponse(serialize_storage_provider(request, sp, permission=True))
    elif request.method == 'POST':
        data = json.loads(request.body)
        action = request.GET.get('action')
        if action not in ('basic', 'permissions'):
            return generate_error_response('Bad request')

        with transaction.atomic():
            if action == 'basic':
                sp.name = data[StorageProviderRequest.NAME_KEY]

                old_path = sp.path
                if not os.path.exists(data[StorageProviderRequest.PATH_KEY]):
                    return generate_error_response('Path doesn\'t exist!')
                sp.path = data[StorageProviderRequest.PATH_KEY]
            
                sp.save()

                if sp.path != old_path:
                    perform_index(request, sp.pk)
            elif action == 'permissions':
                StorageProviderUser.objects.filter(
                    storage_provider=sp).delete()

                perms = []
                user_pks = User.objects.all().values_list('pk', flat=True)
                for x in data[StorageProviderRequest.PERMISSION_KEY]:
                    if x['permission'] not in StorageProviderUser.PERMISSIONS:
                        raise Exception('Invalid permission type!')
                    if x['user']['id'] not in user_pks:
                        raise Exception('User not found!')
                    perms.append(StorageProviderUser(
                        storage_provider=sp, permission=x['permission'],
                        user_id=x['user']['id']))
                StorageProviderUser.objects.bulk_create(perms)

        return JsonResponse(serialize_storage_provider(request, sp, True, refresh_cache=True))
    elif request.method == 'DELETE':
        sp.delete()
        cache.delete(sp.pk)
        return JsonResponse({})


@login_required()
@require_GET
@catch_error
def get_storage_provider_permissions(request):
    values = [
        {'name': x[1], 'value': x[0]}
        for x in StorageProviderUser.PERMISSION_CHOICES
    ]
    return JsonResponse({'values': values})


@login_required()
@require_POST
@catch_error
def perform_index(request, provider_id):
    try:
        sp = StorageProvider.objects.get(pk=provider_id)
    except:
        raise Exception('Provider not found!')

    if not has_storage_provider_permission(
        sp, request.user, StorageProviderUser.PERMISSION.READ_WRITE):
        return generate_error_response(
            'No permission to perform the operation.', status=403)

    for fo in LocalFileObject.objects.select_related('storage_provider').filter(parent=None, storage_provider__pk=provider_id):
        LocalStorageProviderIndexer.sync(fo, True)
    return JsonResponse({})
