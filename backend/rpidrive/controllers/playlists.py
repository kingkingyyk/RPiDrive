from typing import List

from django.conf import settings
from django.contrib.auth.models import User
from django.db import transaction
from django.db.models import Q, QuerySet
from rpidrive.models import Playlist, PlaylistFile


class PlaylistNotFoundException(Exception):
    """Playlist not found exception"""


class InvalidNameException(Exception):
    """Invalid name exception"""


def get_playlists(user: User) -> QuerySet:
    """Get playlists"""
    return Playlist.objects.filter(owner=user)


def get_playlist(
    user: User,
    pl_id: str,
    select_related: List[str] = None,
    prefetch_related: List[str] = None,
    write=False,
) -> Playlist:
    """Get playlist by id"""
    if not select_related:
        select_related = []
    if not prefetch_related:
        prefetch_related = []

    playlist = (
        Playlist.objects.filter(Q(id=pl_id) & Q(owner=user))
        .select_related(*select_related)
        .prefetch_related(*prefetch_related)
    )
    if write:
        playlist = playlist.select_for_update(of=("self",))
    playlist = playlist.first()
    if not playlist:
        raise PlaylistNotFoundException("Playlist not found.")
    return playlist


def create_playlist(user: User, name: str):
    """Create playlist"""
    if not name:
        raise InvalidNameException("Invalid name.")
    name = name.strip()
    if not name:
        raise InvalidNameException("Invalid name.")
    return Playlist.objects.create(
        name=name,
        owner=user,
    )


def update_playlist(user: User, pl_id: str, name: str):
    """Update playlist"""
    if not name:
        raise InvalidNameException()
    name = name.strip()
    if not name:
        raise InvalidNameException()
    with transaction.atomic():
        playlist = get_playlist(user, pl_id, [], [], True)
        playlist.name = name
        playlist.save(update_fields=["name"])
    return playlist


def add_playlist_file(user: User, pl_id: str, file_id: str):
    """Add file to playlist"""
    with transaction.atomic():
        playlist = get_playlist(user, pl_id, [], [], True)
        last_seq = (
            PlaylistFile.objects.filter(playlist=playlist)
            .order_by("sequence")
            .values_list("sequence", flat=True)
            .last()
            or -1
        ) + 1
        PlaylistFile.objects.create(
            playlist=playlist,
            file_id=file_id,
            sequence=last_seq,
        )
    return playlist


def remove_playlist_file(user: User, pl_id: int, file_id: int):
    """Remove playlist file"""
    with transaction.atomic():
        playlist = get_playlist(user, pl_id, None, None, True)
        PlaylistFile.objects.filter(Q(pk=file_id) & Q(playlist=playlist)).delete()
    return playlist


def reorder_playlist_file(user: User, pl_id: str, files: List[int]):
    """Reorder playlist file"""
    with transaction.atomic():
        playlist = get_playlist(user, pl_id, None, ["playlistfile_set"], True)
        reverse_map = {file_id: idx for idx, file_id in enumerate(files)}
        playlist_files = playlist.playlistfile_set.all()
        for file in playlist_files:
            file.sequence = reverse_map.get(file.id, 0)
        PlaylistFile.objects.bulk_update(
            playlist_files, fields=["sequence"], batch_size=settings.BULK_BATCH_SIZE
        )
    return playlist


def delete_playlist(user: User, pl_id: str):
    """Delete playlist"""
    get_playlist(user, pl_id).delete()
