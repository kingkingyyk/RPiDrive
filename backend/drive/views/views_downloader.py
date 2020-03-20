from aria2p import API, Client
from django.views.decorators.http import require_http_methods
from django.conf import settings
from django.http.response import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json


def get_aria2_api():
    return API(Client(host='http://'+settings.ARIA2_HOST, port=settings.ARIA2_PORT, secret=settings.ARIA2_SECRET))


@require_http_methods(["POST"])
@csrf_exempt
def add_url_download(request):
    data = json.loads(request.body)
    if not data['url'].startswith('http://') and not data['url'].startswith('https://'):
        return JsonResponse({'error': 'URL must start with http or https!'}, 400)
    if data['authentication']:
        prefixes = ['http://', 'https://']
        for prefix in prefixes:
            if data['url'].startswith(prefix):
                data = data['url'].replace(
                    prefix, prefix+data['username']+':'+data['password']+'@')
                break
    get_aria2_api().add_uris([data['url']])
    return JsonResponse({})


@require_http_methods(['POST'])
@csrf_exempt
def add_magnet_download(request):
    data = json.loads(request.body)
    if not data['url'].startswith('magnet:?xt='):
        return JsonResponse({'error': 'Invalid magnet link'}, status=400)
    get_aria2_api().add_magnet(data['url'])
    return JsonResponse({})


@require_http_methods(['POST'])
@csrf_exempt
def add_torrent_download(request):
    return JsonResponse({})


def get_downloads(request):
    data = []
    for download in get_aria2_api().get_downloads():
        if download.status in ['active', 'waiting', 'paused']:
            data.append({
                'id': download.gid,
                'name': download.name,
                'status': download.status,
                'downloadSpeed': download.download_speed_string(),
                'progress': download.progress_string()
            })
    data = {'values': data}
    return JsonResponse(data)


@require_http_methods(['PUT'])
@csrf_exempt
def pause_download(request, gid):
    try:
        get_aria2_api().get_download(gid).pause(True)
    except:
        return JsonResponse({}, status=400)
    return JsonResponse({})


@require_http_methods(['PUT'])
@csrf_exempt
def resume_download(request, gid):
    try:
        get_aria2_api().get_download(gid).resume()
    except:
        return JsonResponse({}, status=400)
    return JsonResponse({})


@require_http_methods(['DELETE'])
@csrf_exempt
def cancel_download(request, gid):
    try:
        get_aria2_api().get_download(gid).remove(True, True)
    except:
        return JsonResponse({}, status=400)
    return JsonResponse({})
