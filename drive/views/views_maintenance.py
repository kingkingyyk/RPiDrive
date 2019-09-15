from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from drive.features.downloader import *
from ..enum import *


@login_required
def manage_storage(request):
    drive = Drive.objects.get()
    storages = Storage.objects.all()

    context = {'drive': drive,
               'storages': storages,
               'weekdays': weekdays,
               'storage_sync_period': storage_sync_period,
               }

    return render(request, 'drive/manage-storage.html', context)