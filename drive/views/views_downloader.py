from drive.models import *
from drive.utils.model_utils import ModelUtils
from drive.features.downloader import Downloader
from django.http import HttpResponseBadRequest, JsonResponse
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
import requests, re, os, mimetypes


@login_required
def add(request):
    url = request.POST['url']
    filename = request.POST['filename']
    auth = request.POST['auth'] == 'true'
    auth_user = request.POST['auth-user']
    auth_password = request.POST['auth-password']
    destination_folder = request.POST['destination-folder']

    if len(url) == 0:
        return JsonResponse({'error': 'URL cannot be empty!'}, status=HttpResponseBadRequest.status_code)

    if auth:
        if len(auth_user) == 0:
            return JsonResponse({'error': 'Username cannot be empty!'}, status=HttpResponseBadRequest.status_code)

        if len(auth_password) == 0:
            return JsonResponse({'error': 'Password cannot be empty!'}, status=HttpResponseBadRequest.status_code)

    destination_folder = Folder.objects.filter(id=destination_folder).first()
    if destination_folder is None:
        return JsonResponse({'error': 'Destination folder doesn\'t exist!'}, status=HttpResponseBadRequest.status_code)

    extension = ""
    if filename == "":
        try:
            if auth:
                response = requests.head(url, auth=(auth_user, auth_password),
                                         verify=False, timeout=(settings.DOWNLOADER_CONNECT_TIMEOUT, settings.DOWNLOADER_READ_TIMEOUT),
                                         allow_redirects=True)
            else:
                response = requests.head(url, verify=False, timeout=(settings.DOWNLOADER_CONNECT_TIMEOUT, settings.DOWNLOADER_READ_TIMEOUT),
                                         allow_redirects=True)

            if response.status_code < 400:
                url = response.url
                if "Content-Disposition" in response.headers.keys():
                    filename = re.findall("filename=(.+)", response.headers["Content-Disposition"])
                    filename = filename[0] if filename else ""
                if "Content-Type" in response.headers.keys():
                    extension = mimetypes.guess_extension(response.headers["Content-Type"])
                    if extension is None:
                        extension = ""
            else:
                return JsonResponse({'error': 'File not found!'},
                                    status=HttpResponseBadRequest.status_code)
        except:
            return JsonResponse({'error': 'File not found!'},
                                status=HttpResponseBadRequest.status_code)

        if not filename:
            filename = url.split('/')[-1]

        if not extension:
            extension = '.'+filename.split('.')[-1] if filename != filename.split('.')[-1] else '.download'

        if not filename.endswith(extension):
            filename = filename + extension
    else:
        extension = filename.split('.')[-1]

    rel_path = os.path.join(destination_folder.relative_path, filename)
    real_path = os.path.join(ModelUtils.get_storage().base_path, rel_path)
    if os.path.exists(real_path):
        os.remove(real_path)
        f = File.objects.select_related('download').get(relative_path=rel_path)
        if f.download:
            return JsonResponse({'error': 'The file is associated with download!'},
                                status=HttpResponseBadRequest.status_code)
        open(real_path, 'w+').close()
    else:
        now = datetime.now(tz=get_current_timezone())
        test_filename = now.strftime('%Y%m%d_%H%M%S')
        flag = False

        for idx in range(0, 100):
            try:
                open(real_path, 'w+').close()
                flag = True
                break
            except:
                filename = '{}_{:d}.{}'.format(test_filename, idx, extension)
                rel_path = os.path.join(destination_folder.relative_path, filename)
                real_path = os.path.join(ModelUtils.get_storage().base_path, destination_folder.relative_path, filename)

        if not flag:
            return JsonResponse({'error': 'Failed to write file on storage!'},
                                status=HttpResponseBadRequest.status_code)

        f = File(relative_path=rel_path,
                 parent_folder=destination_folder)
        f.save()

    dl = Download(file=f,
                  source_url=url,
                  auth=auth,
                  username=auth_user,
                  password=auth_password,
                  progress=0.0,
                  status=DownloadStatus.queue.value,
                  to_stop=False,
                  to_delete_file=False,
                  add_time=datetime.now(tz=get_current_timezone()),
                  downloader_status=None)
    dl.save()
    return JsonResponse({})


@login_required
def cancel(request):
    download_id = request.POST['id']
    download = Download.objects.filter(id=download_id).first()
    if download is None:
        return JsonResponse({'error': 'Download doesn\'t exist.'},
                            status=HttpResponseBadRequest.status_code)
    else:
        Downloader.interrupt(download)
    return JsonResponse({})


@login_required
def list(request):
    downloads = Download.objects.all()

    context = {'downloads': downloads,
               }

    return render(request, 'drive/manage-downloads.html', context)