import http
import json
import os

from typing import Any, List, Optional

from django.db import transaction
from django.db.models import Prefetch
from django.http.response import JsonResponse
from django.views.decorators.http import (
    require_GET,
    require_POST,
    require_http_methods,
)
from pydantic import BaseModel, Field

from drive.core.local_file_object import update_file_metadata
from drive.models import (
    LocalFileObject,
    Playlist,
    PlaylistFile,
)
from drive.views.web.shared import (
    generate_error_response,
    login_required_401,
)

class PlaylistFileModel(BaseModel):
    """Playlist file model"""
    id: str
    name: str
    type: str
    metadata: Any
    fullPath: str

class PlaylistModel(BaseModel):
    """Playlist model"""
    id: str
    name: str
    files: Optional[List[PlaylistFileModel]]

class PlaylistCreationModel(BaseModel):
    """Playlist creation model"""
    name: str = Field(..., min_length=1)

class PlaylistUpdateModel(BaseModel):
    """Playlist update model"""
    name: Optional[str]
    files: Optional[List[str]]

def serialize_playlist(playlist: Playlist, load_list: bool=True):
    """Convert playlist object to dictionary"""
    playlist_obj = PlaylistModel(
        id=str(playlist.pk),
        name=playlist.name,
    )
    if load_list:
        playlist_obj.files = [
            PlaylistFileModel(
                id=str(x.file.pk),
                name=x.file.name,
                type=x.file.type,
                metadata=x.file.metadata,
                fullPath=os.path.join(x.file.storage_provider.path, x.file.rel_path)
            ) for x in playlist.files.all()
        ]
    return playlist_obj.dict()

@login_required_401
@require_GET
def get_playlists(request):
    """Return playlists owned by user"""
    playlists = Playlist.objects.filter(
        owner=request.user).order_by('name').all()
    return JsonResponse(dict(
        values=[serialize_playlist(x, False) for x in playlists]
    ))

@login_required_401
@require_POST
def create_playlist(request):
    """Create playlist"""
    data = PlaylistCreationModel.parse_obj(json.loads(request.body))
    playlist = Playlist(
        name=data.name,
        owner=request.user,
    )
    playlist.save()
    return JsonResponse(
        serialize_playlist(playlist),
        status=http.HTTPStatus.CREATED,
    )

@login_required_401
@require_http_methods(['GET', 'POST', 'DELETE'])
def manage_playlist(request, playlist_id):
    """Read/update/delete playlist"""
    playlist = (
        Playlist.objects
        .prefetch_related(Prefetch(
            'files',
            queryset=PlaylistFile.objects.select_related('file', 'file__storage_provider')
        )).filter(
            pk=playlist_id,
            owner=request.user,
        ).first()
    )
    if not playlist:
        return generate_error_response(
            'Playlist not found.',
            status=http.HTTPStatus.NOT_FOUND
        )

    if request.method == 'GET':
        for p_f in playlist.files.all():
            update_file_metadata(p_f.file)
        return JsonResponse(serialize_playlist(playlist))

    if request.method == 'POST':
        data = PlaylistUpdateModel.parse_obj(json.loads(request.body))
        with transaction.atomic():
            playlist = (
                Playlist.objects
                .select_for_update(of=('self',))
                .get(pk=playlist_id)
            )

            if data.name:
                playlist.name = data.name

            if data.files:
                playlist.files.clear()
                files = LocalFileObject.objects.filter(pk__in=data.files).all()
                files_dict = {str(x.pk): x for x in files}
                for idx, f_pk in enumerate(data.files):
                    file = files_dict[f_pk]
                    playlist.files.add(file, through_defaults={'sequence': idx})

            playlist.save()
        return JsonResponse({})

    if request.method == 'DELETE':
        playlist.delete()
        return JsonResponse({})

    return generate_error_response(
        {}, status=http.HTTPStatus.METHOD_NOT_ALLOWED
    )
