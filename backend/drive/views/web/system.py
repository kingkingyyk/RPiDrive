from django.http.response import JsonResponse
from django.views.decorators.http import require_GET, require_POST, require_http_methods
from django.contrib.auth.models import User
from django.db import transaction
from ...models import System, StorageProvider
from ...core.storage_provider import create_storage_provider_helper
from .storage_provider import StorageProviderRequest
from .shared import generate_error_response
import json

class InitializeSystemRequest:
    INIT_KEY = 'initKey'
    STORAGE_PROVIDER_KEY = 'storageProvider'
    USER_KEY = 'user'

class CreateUserRequest:
    USERNAME_KEY = 'username'
    PASSWORD_KEY = 'password'
    FIRST_NAME_KEY = 'firstName'
    LAST_NAME_KEY = 'lastName'
    EMAIL_KEY = 'email'
    ACTIVE_KEY = 'isActive'
    SUPERUSER_KEY = 'isSuperuser'

@require_http_methods(['GET', 'POST'])
def initialize_system(request):
    sys, created = System.objects.get_or_create()
    if created:
        print('Initialization Key : {}'.format(sys.init_key))
    if request.method == 'GET':
        if not sys.initialized:
            return JsonResponse({}, status=200)
        else:
            return generate_error_response('', status=401)
    elif request.method == 'POST':
        if sys.initialized:
            return generate_error_response('System has already been initialized!')
        data = json.loads(request.body)
        if data[InitializeSystemRequest.INIT_KEY] != sys.init_key:
            return generate_error_response('Invalid initialization key! Please check server console.',
                                           status=401)

        with transaction.atomic():
            # Create superuser
            user_data = data[InitializeSystemRequest.USER_KEY]
            user = User(username=user_data[CreateUserRequest.USERNAME_KEY],
                 first_name=user_data[CreateUserRequest.FIRST_NAME_KEY],
                 last_name=user_data[CreateUserRequest.LAST_NAME_KEY],
                 email=user_data[CreateUserRequest.EMAIL_KEY],
                 is_active=user_data[CreateUserRequest.ACTIVE_KEY],
                 is_staff=True,
                 is_superuser=user_data[CreateUserRequest.SUPERUSER_KEY])
            user.set_password(user_data[CreateUserRequest.PASSWORD_KEY])
            user.save()

            # Create storage provider
            sp_data = data[InitializeSystemRequest.STORAGE_PROVIDER_KEY]
            try:
                StorageProviderRequest.inspect_create_data(sp_data)
            except Exception as e:
                return generate_error_response(str(e))

            create_storage_provider_helper(name=sp_data[StorageProviderRequest.NAME_KEY],
                                           type=sp_data[StorageProviderRequest.TYPE_KEY],
                                           path=sp_data[StorageProviderRequest.PATH_KEY])

            # Flag system as initialized
            System.objects.update(initialized=True)

        return JsonResponse({}, status=200)
