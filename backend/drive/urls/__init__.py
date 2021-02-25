from .web import urlpatterns as web
from drive.views.web import request_download_file
from django.shortcuts import render
from django.urls import path, include, re_path

def index(request, **kwargs):
    return render(request, 'drive/index.html')

urlpatterns = [
    path(r'web-api/', include('drive.urls.web')),
    path(r'download/<str:file_id>', request_download_file),

    re_path(r'^(?P<path>.*)/$', index),
    re_path(r'$', index),
]