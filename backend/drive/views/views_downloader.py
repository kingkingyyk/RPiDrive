from aria2p import API, Client
from django.views.decorators.http import require_http_methods
from django.conf import settings
from django.http.response import JsonResponse
from . import requires_login
import json


def get_aria2_api():
    return API(Client(host='http://'+settings.ARIA2_HOST, port=settings.ARIA2_PORT, secret=settings.ARIA2_SECRET))


@require_http_methods(["POST"])
@requires_login
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
@requires_login
def add_magnet_download(request):
    data = json.loads(request.body)
    if not data['url'].startswith('magnet:?xt='):
        return JsonResponse({'error': 'Invalid magnet link'}, status=400)
    get_aria2_api().add_magnet(data['url'])
    return JsonResponse({})


@require_http_methods(['POST'])
@requires_login
def add_torrent_download(request):
    return JsonResponse({})

@requires_login
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
@requires_login
def pause_download(request, gid):
    try:
        get_aria2_api().get_download(gid).pause(True)
    except:
        return JsonResponse({}, status=400)
    return JsonResponse({})


@require_http_methods(['PUT'])
@requires_login
def resume_download(request, gid):
    try:
        get_aria2_api().get_download(gid).resume()
    except:
        return JsonResponse({}, status=400)
    return JsonResponse({})


@require_http_methods(['DELETE'])
@requires_login
def cancel_download(request, gid):
    try:
        get_aria2_api().get_download(gid).remove(True, True)
    except:
        return JsonResponse({}, status=400)
    return JsonResponse({})

def update_disk_cache():
    options = get_aria2_api().get_global_options()
    options.disk_cache = settings.ARIA2_DISK_CACHE
    get_aria2_api().set_global_options(options)