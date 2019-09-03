from .models import *
from .views import get_storage
from django.http import HttpResponse, HttpResponseBadRequest
import requests, re, os, json
from django.contrib.auth.decorators import login_required


@login_required
def add(request):
    url = request.POST['url']
    auth = request.POST['auth'] == 'true'
    auth_user = request.POST['auth-user']
    auth_password = request.POST['auth-password']
    destination_folder = request.POST['destination-folder']

    if len(url) == 0:
        return HttpResponseBadRequest(json.dumps({'error': 'URL cannot be empty!'}), content_type='application/json')

    if auth:
        if len(auth_user) == 0:
            return HttpResponseBadRequest(json.dumps({'error': 'Username cannot be empty!'}),
                                          content_type='application/json')
        if len(auth_password) == 0:
            return HttpResponseBadRequest(json.dumps({'error': 'Password cannot be empty!'}),
                                          content_type='application/json')

    destination_folder = Folder.objects.filter(id=destination_folder).first()
    if destination_folder is None:
        return HttpResponseBadRequest(json.dumps({'error': 'Destination folder doesn\'t exist!'}), content_type='application/json')

    filename = ""
    try:
        if auth:
            response = requests.head(url, auth=(auth_user, auth_password), verify=False, timeout=10)
        else:
            response = requests.head(url, verify=False, timeout=10)

        if response.status_code < 400:
            if "Content-Disposition" in response.headers.keys():
                filename = re.findall("filename=(.+)", response.headers["Content-Disposition"])
                filename = filename[0] if filename else ""
        else:
            return HttpResponseBadRequest(json.dumps({'error': 'File not found!'}), content_type='application/json')
    except:
        return HttpResponseBadRequest(json.dumps({'error': 'File not found!'}), content_type='application/json')

    if len(filename) == 0:
        filename = url.split("/")[-1]

    rel_path = os.path.join(destination_folder.relative_path, filename)
    real_path = os.path.join(get_storage().base_path, rel_path)
    if os.path.exists(real_path):
        os.remove(real_path)
        f = File.objects.get(relative_path=rel_path)
        if Download.objects.filter(file=f).exists():
            return HttpResponseBadRequest(json.dumps({'error': 'The file is associated with download!'}), content_type='application/json')
    else:
        f = File(relative_path=rel_path,
                 last_modified=datetime.now(tz=get_current_timezone()),
                 size=0,
                 parent_folder=destination_folder)
        f.save()

    open(real_path, 'w+').close()
    dl = Download(file=f,
                  source_url=url,
                  auth=auth,
                  username=auth_user,
                  password=auth_password,
                  progress=0.0,
                  status=DownloadStatus.queue.value)
    dl.save()

    return HttpResponse('{}', content_type='application/json')
