from django.http.response import JsonResponse
from django.views.decorators.http import require_GET, require_POST, require_http_methods
from drive.models import *
from .local_file_object import *
from .shared import *
import json

class StorageProviderRequest:
    ID_KEY = 'name'
    NAME_KEY = 'name'
    TYPE_KEY = 'type'
    PATH_KEY = 'path'

    @staticmethod
    def _inspect_type(sp_type):
        if sp_type not in StorageProviderType.VALUES:
            raise Exception('The provider type is incorrect! Supported types are {}!'.format(', '.join(StorageProviderType.VALUES)))

    @staticmethod
    def inspect_create_data(data):
        NEEDED_KEYS = [StorageProviderRequest.NAME_KEY, StorageProviderRequest.TYPE_KEY, StorageProviderRequest.PATH_KEY]
        missing = [x for x in NEEDED_KEYS if x not in data.keys()]
        if missing:
            raise Exception('The following fields ({}) are missing!'.format(', '.join(missing)))
        StorageProviderRequest._inspect_type(data[StorageProviderRequest.TYPE_KEY])

def serialize_storage_provider(request, sp):
    return {
        StorageProviderRequest.ID_KEY: sp.pk,
        StorageProviderRequest.NAME_KEY: sp.name,
        StorageProviderRequest.TYPE_KEY: sp.type,
        StorageProviderRequest.PATH_KEY: sp.path,
    }


@require_GET
def get_storage_provider_types(request):
    data = [
        {
            'name': x[0],
            'value': x[1],
        } for x in StorageProviderType.TYPES
    ]
    return JsonResponse({'values': data})


@require_GET
def get_storage_providers(request):
    data = [
        serialize_storage_provider(request, x) for x in StorageProvider.objects.all()
    ]
    return JsonResponse({'values': data})


@require_POST
def create_storage_provider(request):
    data = json.loads(request.body)

    try:
        StorageProviderRequest.inspect_create_data(data)
    except Exception as e:
        return generate_error_response(str(e))

    sp = StorageProvider(
        name = data[StorageProviderRequest.NAME_KEY],
        type = data[StorageProviderRequest.TYPE_KEY],
        path = data[StorageProviderRequest.PATH_KEY],
    )
    sp.save()
    return JsonResponse(serialize_storage_provider(request, sp))

@require_http_methods(['GET', 'POST', 'DELETE'])
def manage_storage_provider(request, provider_id):
    try:
        sp = StorageProvider.objects.get(pk=provider_id)
    except:
        raise Exception('Provider not found!')
    if request.method == 'GET':
        return JsonResponse(serialize_storage_provider(sp))
    elif request.method == 'POST':
        pass
    elif request.method == 'DELETE':
        sp.delete()
        return JsonResponse({})

@require_POST
def perform_index(request, provider_id):
    pass
