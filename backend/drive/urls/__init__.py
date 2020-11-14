from .web import urlpatterns as web
from django.urls import path, include

urlpatterns = [
    path(r'web-api', include('drive.urls.web')),
]