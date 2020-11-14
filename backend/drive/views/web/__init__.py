from .storage_provider import *
from .local_file_object import *

def generate_error_response(msg):
    return JsonResponse({'error': msg}, status=400)