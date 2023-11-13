from enum import Enum
from typing import List

from django.http.response import JsonResponse
from django.views import View
from pydantic import BaseModel, ValidationError
from rpidrive.controllers.playlists import (
    InvalidNameException,
    add_playlist_file,
    delete_playlist,
    get_playlist,
    reorder_playlist_file,
    remove_playlist_file,
    update_playlist,
)
from rpidrive.views.decorators.generics import handle_exceptions


class _ActionEnum(str, Enum):
    RENAME = "rename"
    ADD_FILE = "add-file"
    REMOVE_FILE = "remove-file"
    REORDER = "reorder"


class _RequestModel(BaseModel):
    action: _ActionEnum


class _RenameModel(BaseModel):
    name: str


class _AddFileModel(BaseModel):
    file_id: str


class _RemoveFileModel(BaseModel):
    file_id: int


class _ReorderModel(BaseModel):
    files: List[int]


class PlaylistDetailView(View):
    """Playlist detail view"""

    _ACTION_MODEL_MAP = {
        _ActionEnum.RENAME: _RenameModel,
        _ActionEnum.ADD_FILE: _AddFileModel,
        _ActionEnum.REMOVE_FILE: _RemoveFileModel,
        _ActionEnum.REORDER: _ReorderModel,
    }
    _ACTION_METHOD_MAP = {
        _ActionEnum.RENAME: update_playlist,
        _ActionEnum.ADD_FILE: add_playlist_file,
        _ActionEnum.REMOVE_FILE: remove_playlist_file,
        _ActionEnum.REORDER: reorder_playlist_file,
    }

    def get(self, request, playlist_id: str, *_args, **_kwargs) -> JsonResponse:
        """Handle GET request"""
        playlist = get_playlist(
            request.user,
            playlist_id,
            [],
            ["playlistfile_set", "playlistfile_set__file"],
        )
        data = {
            "id": playlist.id,
            "name": playlist.name,
            "files": [
                {
                    "id": x.id,
                    "source_id": x.file.id,
                    "name": x.file.name,
                    "metadata": x.file.metadata,
                }
                for x in playlist.playlistfile_set.order_by("sequence").all()
            ],
        }
        return JsonResponse(data)

    @handle_exceptions(
        known_exc={
            InvalidNameException,
            ValidationError,
        }
    )
    def post(self, request, playlist_id: str, *_args, **_kwargs) -> JsonResponse:
        """Handle POST request"""
        data = _RequestModel.model_validate_json(request.body)
        act_data: BaseModel = self._ACTION_MODEL_MAP[data.action].model_validate_json(
            request.body
        )
        playlist = self._ACTION_METHOD_MAP[data.action](
            request.user, playlist_id, **act_data.model_dump()
        )
        return JsonResponse({"id": playlist_id, "name": playlist.name})

    def delete(self, request, playlist_id: str, *_args, **_kwargs) -> JsonResponse:
        """Handle DELETE request"""
        delete_playlist(request.user, playlist_id)
        return JsonResponse({})
