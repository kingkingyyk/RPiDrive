from django.http.response import JsonResponse

def generate_error_response(msg):
    return JsonResponse({'error': msg}, status=400)