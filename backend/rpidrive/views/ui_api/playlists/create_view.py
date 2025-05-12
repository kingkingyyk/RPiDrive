import http

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http.response import JsonResponse
from django.views import View
from pydantic import BaseModel, ValidationError

from rpidrive.controllers.playlists import (
    InvalidNameException,
    create_playlist,
)
from rpidrive.views.decorators.generics import handle_exceptions


class _RequestModel(BaseModel):
    name: str


class PlaylistCreateView(LoginRequiredMixin, View):
    """Playlist create view"""

    @handle_exceptions(
        known_exc={
            InvalidNameException,
            ValidationError,
        }
    )
    def post(self, request, *_args, **_kwargs) -> JsonResponse:
        """Handle GET request"""
        data = _RequestModel.model_validate_json(request.body)
        playlist = create_playlist(request.user, data.name)
        return JsonResponse(
            {"id": playlist.id, "name": playlist.name}, status=http.HTTPStatus.CREATED
        )
