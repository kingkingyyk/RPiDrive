from django.http.response import JsonResponse

def generate_error_response(msg, status=400):
    return JsonResponse({'error': msg}, status=status)