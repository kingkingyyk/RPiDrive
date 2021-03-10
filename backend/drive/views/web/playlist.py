import json
import os
from django.db import transaction
from django.db.models import Prefetch
from django.http.response import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_GET, require_POST, require_http_methods
from drive.core.local_file_object import update_file_metadata
from drive.models import (
    LocalFileObject,
    Playlist,
    PlaylistFile,
)
from drive.views.web.shared import generate_error_response


def serialize_playlist(playlist: Playlist, load_list: bool=True):
    """Convert playlist object to dictionary"""
    ret = {
        'id': playlist.pk,
        'name': playlist.name,
    }
    if load_list:
        ret['files'] = [{
            'id': x.file.pk,
            'name': x.file.name,
            'type': x.file.type,
            'metadata': x.file.metadata,
            'fullPath': os.path.join(x.file.storage_provider.path, x.file.rel_path)
        } for x in playlist.files.all()]
    return ret

@login_required()
@require_GET
def get_playlists(request):
    """Return playlists owned by user"""
    playlists = Playlist.objects.filter(
        owner=request.user).order_by('name').all()
    ret = {'values': [serialize_playlist(x, False) for x in playlists]}
    return JsonResponse(ret)

@login_required()
@require_POST
def create_playlist(request):
    """Create playlist"""
    data = json.loads(request.body)
    playlist = Playlist(name=data['name'],
                        owner=request.user)
    playlist.save()
    return JsonResponse(serialize_playlist(playlist))

@login_required()
@require_http_methods(['GET', 'POST', 'DELETE'])
def manage_playlist(request, playlist_id):
    """Read/update/delete playlist"""
    playlist = Playlist.objects.prefetch_related(Prefetch(
        'files',
        queryset=PlaylistFile.objects.select_related('file', 'file__storage_provider')
            )).filter(pk=playlist_id).first()
    if not playlist:
        return generate_error_response('Playlist not found', status=404)
    if request.method == 'GET':
        for p_f in playlist.files.all():
            update_file_metadata(p_f.file)
        return JsonResponse(serialize_playlist(playlist))
    if request.method == 'POST':
        data = json.loads(request.body)
        with transaction.atomic():
            playlist = Playlist.objects.select_for_update(of=('self',)).get(pk=playlist_id)

            if 'name' in data:
                playlist.name = data['name']

            if 'files' in data:
                playlist.files.clear()
                files = LocalFileObject.objects.filter(pk__in=data['files']).all()
                files_dict = {str(x.pk): x for x in files}
                for idx, f_pk in enumerate(data['files']):
                    file = files_dict[f_pk]
                    playlist.files.add(file, through_defaults={'sequence': idx})

            playlist.save()
        return JsonResponse({})
    if request.method == 'DELETE':
        playlist.delete()
        return JsonResponse({})
    return generate_error_response({}, status=405)
