from django.http.response import JsonResponse
from django.views.decorators.http import require_GET, require_POST, require_http_methods
from drive.models import *

def serialize_file_object(request, file, resolve_parent):
    pass

@require_POST
def create_file(request):
    pass

@require_http_methods(['GET', 'POST', 'DELETE'])
def manage_file(request, file_id):
    pass

@require_POST
def move_file(request, file_id):
    pass

@require_GET
def get_file_metadata(request, file_id):
    pass