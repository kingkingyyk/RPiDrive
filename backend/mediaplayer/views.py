from django.shortcuts import render, get_object_or_404
from django.db import transaction
from django.db.models import Q
from django.http.response import JsonResponse
from mediaplayer.models import *
import json
from django.views.decorators.http import require_http_methods
from drive.views import requires_login, get_user


def serialize_media(media):
    return {
        'id': media.pk,
        'name': media.name,
        'relative_path': media.relative_path,
        'title': media.title,
        'artist': media.artist,
        'album': media.album,
        'genre': media.genre
    }


def search_media(request):
    name = request.GET.get('name', '')
    media = MusicFileObject.objects.filter(Q(name__icontains=name) | Q(relative_path__icontains=name) | Q(
        artist__icontains=name) | Q(album__icontains=name) | Q(genre__icontains=name)).order_by('relative_path').all()[:30]
    data = [serialize_media(x) for x in media]
    data = {'values': data}
    return JsonResponse(data)


def serialize_playlist(playlist, include_media_list):
    qs = FileInPlaylist.objects.filter(
        playlist=playlist).select_related('file').order_by('index').values_list('file__pk')
    data = {
        'id': playlist.pk,
        'name': playlist.name,
        'user': playlist.user.first_name + ' ' + playlist.user.last_name,
        'mediaCount': qs.count(),
        'files': [
        ]
    }
    if include_media_list:
        media_pks = [x[0] for x in qs.all()]
        music = {x.pk: x for x in MusicFileObject.objects.filter(pk__in=media_pks).all()}
        qs = [music[x[0]] for x in qs.all()]
        data['files'] = [serialize_media(x)
                         for x in qs]
    return data

@requires_login
def search_playlists(request):
    name = request.GET.get('name', '')
    playlists = Playlist.objects.prefetch_related('user').filter(
        name__icontains=name).order_by('name').all()
    data = [serialize_playlist(x, False) for x in playlists]
    data = {'values': data}
    return JsonResponse(data)

@requires_login
def get_playlists(request):
    playlists = Playlist.objects.prefetch_related(
        'user').order_by('name').all()
    data = [serialize_playlist(x, False) for x in playlists]
    data = {'values': data}
    return JsonResponse(data)


@require_http_methods(['POST'])
@requires_login
def create_playlist(request):
    user = get_user(request)
    data = json.loads(request.body)
    p = Playlist(name=data['name'], user=user)
    p.save()
    return JsonResponse(serialize_playlist(p, False))


@require_http_methods(['POST', 'GET', 'DELETE'])
@requires_login
def manage_playlist(request, playlist_id):
    if request.method == 'GET':
        playlist = get_object_or_404(Playlist, pk=playlist_id)
        return JsonResponse(serialize_playlist(playlist, True))
    elif request.method == 'POST':
        data = json.loads(request.body)
        with transaction.atomic():
            playlist = get_object_or_404(
                Playlist.objects.select_for_update(), pk=playlist_id)
            if playlist.name != data['name']:
                playlist.name = data['name']
                playlist.save()
            existing_files = [str(x.file.pk) for x in FileInPlaylist.objects.select_related('file').filter(playlist=playlist).all()]
            new_files = [x['id'] for x in data['files']]
            if existing_files != new_files:
                FileInPlaylist.objects.filter(playlist=playlist).all().delete()
                file_obj = File.objects.filter(pk__in=new_files).all()
                file_obj_map = {str(x.pk):x for x in file_obj}
                counter = 0
                for new_file_pk in new_files:
                    if new_file_pk in file_obj_map.keys():
                        FileInPlaylist(playlist=playlist, file=file_obj_map[new_file_pk], index=counter).save()
                        counter += 1
        return JsonResponse(serialize_playlist(playlist, True))
    elif request.method == 'DELETE':
        with transaction.atomic():
            playlist = get_object_or_404(
                Playlist.objects.select_for_update(), pk=playlist_id)
            playlist.delete()
    return JsonResponse({})