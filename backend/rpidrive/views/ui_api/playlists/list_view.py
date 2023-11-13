from django.contrib.auth.mixins import LoginRequiredMixin
from django.http.response import JsonResponse
from django.views import View
from rpidrive.controllers.playlists import get_playlists


class PlaylistListView(LoginRequiredMixin, View):
    """Playlist list view"""

    def get(self, request, *_args, **_kwargs) -> JsonResponse:
        """Handle GET request"""
        playlists = get_playlists(request.user).order_by("name").all()
        return JsonResponse(
            {
                "values": [
                    {
                        "id": playlist.pk,
                        "name": playlist.name,
                    }
                    for playlist in playlists
                ]
            }
        )
