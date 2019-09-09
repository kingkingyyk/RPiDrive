from django.shortcuts import render, redirect, reverse, get_object_or_404
from django.http import HttpResponseBadRequest, StreamingHttpResponse, HttpResponse
from django.contrib.auth.decorators import login_required
from wsgiref.util import FileWrapper
from drive.features.downloader import *
import os, time, mimetypes, traceback, json
from ..utils.model_utils import ModelUtils
from ..utils.file_utils import FileUtils
from ..utils.connection_utils import range_re, RangeFileWrapper

@login_required
def index(request):
    drive = Drive.objects.get()
    folder = ModelUtils.get_folder_by_id(request.GET.get('folder', ModelUtils.get_folder_by_id('').id))
    storages = [Storage.objects.get(primary=True)] + [x for x in Storage.objects.filter(primary=False).order_by('base_path').all()]

    context = {'drive': drive,
               'storages': storages,
               'curr_folder': folder,
               }
    return render(request, 'drive/index.html', context)


@login_required
def ongoing_tasks(request):
    downloads = Download.objects\
                .filter(status__in=(DownloadStatus.downloading.value, DownloadStatus.queue.value))\
                .order_by('status').all()
    context = {
               'downloads': downloads,
               }
    return render(request, 'drive/ongoing-tasks.html', context)


@login_required
def navigate(request, folder_id):
    storage = ModelUtils.get_storage()
    folder = ModelUtils.get_folder_by_id(folder_id)

    #Lazy create file record if needed
    real_path = os.path.join(storage.base_path, folder.relative_path)
    for f in os.listdir(real_path):
        f_real_path = os.path.join(real_path, f)
        cls = File if os.path.isfile(f_real_path) else Folder
        f_obj = cls.objects.filter(relative_path=os.path.join(folder.relative_path, f)).first()
        if f_obj is None:
            cls(relative_path=os.path.join(folder.relative_path, f),
                parent_folder=folder
                ).save()

    #Lazy delete file record if needed
    folders_in_fs = [x for x in os.listdir(real_path) if os.path.isdir(os.path.join(real_path, x))]
    folder_objs = [x for x in Folder.objects.filter(parent_folder=folder).all()]
    for f in [x for x in folder_objs if x.name not in folders_in_fs]:
        f.delete()

    files_in_fs = [x for x in os.listdir(real_path) if os.path.isfile(os.path.join(real_path, x))]
    file_objs = [x for x in File.objects.filter(parent_folder=folder).all()]
    for f in [x for x in file_objs if x.name not in files_in_fs]:
        f.delete()

    #Prepare template data
    file_objs = sorted([x for x in Folder.objects.filter(parent_folder=folder).all()], key=lambda x: x.name) + \
                sorted([x for x in File.objects.filter(parent_folder=folder).all()], key=lambda x: x.name)
    ancestors = []
    ancestor_folder = folder
    while ancestor_folder is not None:
        ancestor_folder = ancestor_folder.parent_folder
        ancestors.append(ancestor_folder)
    ancestors = ancestors[:-2] # Don't need the root.
    ancestors.reverse()

    context = {
        'curr_folder': folder,
        'file_objs': file_objs,
        'ancestors': ancestors,
    }
    return render(request, 'drive/navigate.html', context)


@login_required
def download(request, file_id):
    storage = ModelUtils.get_storage()
    file = get_object_or_404(File, id=file_id)

    download_of_file = Download.objects.filter(file=file).first()
    if download_of_file is not None and not download_of_file.operation_done:
        return HttpResponseBadRequest(json.dumps({'error': 'File is being downloaded!'}), content_type='application/json')

    f_real_path = os.path.join(storage.base_path, file.relative_path)

    range_header = request.META.get('HTTP_RANGE', '').strip()
    range_match = range_re.match(range_header)
    size = os.path.getsize(f_real_path)
    content_type, encoding = mimetypes.guess_type(f_real_path)
    content_type = content_type or 'application/octet-stream'
    if range_match:
        first_byte, last_byte = range_match.groups()
        first_byte = int(first_byte) if first_byte else 0
        last_byte = int(last_byte) if last_byte else size - 1
        if last_byte >= size:
            last_byte = size - 1
        length = last_byte - first_byte + 1
        resp = StreamingHttpResponse(RangeFileWrapper(open(f_real_path, 'rb'), offset=first_byte, length=length), status=206, content_type=content_type)
        resp['Content-Length'] = str(length)
        resp['Content-Range'] = 'bytes %s-%s/%s' % (first_byte, last_byte, size)
    else:
        resp = StreamingHttpResponse(FileWrapper(open(f_real_path, 'rb')), content_type=content_type)
        resp['Content-Length'] = str(size)
    resp['Content-Disposition'] = 'filename='+file.name
    resp['Accept-Ranges'] = 'bytes'
    return resp


@login_required
def create_folder(request, folder_id):
    new_folder_name = request.POST['name']
    storage = ModelUtils.get_storage()
    folder = ModelUtils.get_folder_by_id(folder_id)

    new_folder_rel_path = os.path.join(folder.relative_path, new_folder_name)
    new_folder_real_path = os.path.join(storage.base_path, new_folder_rel_path)
    if os.path.exists(new_folder_real_path):
        return HttpResponseBadRequest(json.dumps({'error': 'Folder already exists'}), content_type='application/json')

    try:
        os.mkdir(new_folder_real_path)
        Folder (relative_path=new_folder_rel_path,
                parent_folder=folder
                ).save()
        f = Folder.objects.get(relative_path=new_folder_rel_path)
        return HttpResponse(json.dumps({'id': str(f.id)}), content_type='application/json')
    except:
        return HttpResponseBadRequest(json.dumps({'error': str(traceback.format_exc())}), content_type='application/json')


@login_required
def delete_file_objects(request):
    try:
        storage = ModelUtils.get_storage()
        delete_ids = request.POST['delete-ids'].split(',')
        file_obj = FileObject.objects.filter(id__in=delete_ids).all()

        for f in file_obj:
            if f.size_natural != '-' and Download.objects.filter(file=f).first() and not Download.objects.get(file=f).operation_done:
                Downloader.interrupt(Download.objects.get(file=f))
            else:
                FileUtils.delete_file_or_dir(os.path.join(storage.base_path, f.relative_path))
                f.delete()

        return HttpResponse('{}', content_type='application/json')
    except:
        return HttpResponseBadRequest(json.dumps({'error': str(traceback.format_exc())}), content_type='application/json')


@login_required
def rename_file_object(request, file_obj_id):
    new_name = request.POST['name']
    storage = ModelUtils.get_storage()
    file_obj = FileObject.objects.filter(id=file_obj_id).first()
    if file_obj is None:
        return HttpResponseBadRequest(json.dumps({'error': 'Item not exists.'}), content_type='application/json')

    file_obj_real_path = os.path.join(storage.base_path, file_obj.relative_path)
    if not os.path.exists(file_obj_real_path):
        return HttpResponseBadRequest(json.dumps({'error': 'Item not exists.'}), content_type='application/json')

    file_obj_new_rel_path = os.path.join(file_obj.parent_folder.relative_path, new_name)
    file_obj_new_real_path = os.path.join(storage.base_path, file_obj_new_rel_path)
    if os.path.exists(file_obj_new_real_path):
        return HttpResponseBadRequest(json.dumps({'error': 'Another file with name ' + new_name + ' already exists.'}), content_type='application/json')

    try:
        os.rename(file_obj_real_path, file_obj_new_real_path)
        file_obj.relative_path = file_obj_new_rel_path
        file_obj.save()
        return HttpResponse('{}', content_type='application/json')
    except:
        return HttpResponseBadRequest(json.dumps({'error': str(traceback.format_exc())}),
                                      content_type='application/json')


@login_required
def move_file_object(request):
    try:
        storage = ModelUtils.get_storage()
        to_move_ids = request.POST['to-move-ids'].split(',')
        destination_id = request.POST['destination-id']

        file_objs = FileObject.objects.filter(id__in=to_move_ids).all()
        destination_folder = ModelUtils.get_folder_by_id(destination_id)

        file_obj_rel_paths = [x.relative_path for x in file_objs]
        prohibited_folders = []
        for folder in Folder.objects.all():
            flag = False
            for p in file_obj_rel_paths:
                if folder.relative_path.startswith(p):
                    flag = True
                    break
            if flag:
                prohibited_folders.append(folder)

        if destination_folder in prohibited_folders:
            return HttpResponseBadRequest(json.dumps({'error': 'Destination folder cannot be the selected folder and the subfolders!'}),
                                          content_type='application/json')

        for file_obj in file_objs:
            file_obj_old_real_path = os.path.join(storage.base_path, file_obj.parent_folder.relative_path, file_obj.name)
            exp_file_obj_new_real_path = os.path.join(storage.base_path, destination_folder.relative_path, file_obj.name)
            file_obj_new_real_path = exp_file_obj_new_real_path
            idx = 1
            while os.path.exists(file_obj_new_real_path):
                prefix = '.'.join(exp_file_obj_new_real_path.split('.')[:-1])
                ext = exp_file_obj_new_real_path.split('.')[-1]
                file_obj_new_real_path = '{}_{:d}.{}'.format(prefix, idx, ext)
                idx += 1
            shutil.move(file_obj_old_real_path, file_obj_new_real_path)
            file_obj.relative_path = os.path.join(destination_folder.relative_path, file_obj_new_real_path.split(os.path.sep)[-1])
            file_obj.parent_folder = destination_folder
        return HttpResponse('{}', content_type='application/json')
    except:
        return HttpResponseBadRequest(json.dumps({'error': str(traceback.format_exc())}), content_type='application/json')


@login_required
def list_folders(request, folder_id):
    folder = ModelUtils.get_folder_by_id(folder_id)
    folder_list = Folder.objects.filter(parent_folder=folder).order_by('relative_path').all()
    context = {
        'curr_folder': folder,
        'folder_list': folder_list,
    }
    return render(request, 'drive/move-table.html', context)


@login_required
def upload_files(request, folder_id):
    folder = ModelUtils.get_folder_by_id(folder_id)
    if request.method == 'POST' and request.FILES['files-to-upload']:
        for temp_file_obj in request.FILES.getlist('files-to-upload'):
            f_real_path = os.path.join(ModelUtils.get_storage().base_path, folder.relative_path, temp_file_obj.name)
            if os.path.exists(f_real_path):
                FileUtils.delete_file_or_dir(f_real_path)
            with open(f_real_path, 'wb+') as f:
                shutil.copyfileobj(temp_file_obj.file, f, 10485760)
    return redirect(reverse('index')+'?folder='+folder_id)