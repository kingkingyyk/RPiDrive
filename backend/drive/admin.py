from django.contrib import admin
from .models import Settings, Storage, FolderObject, FileObject, PictureFileObject, MusicFileObject

# Register your models here.
admin.site.register(Settings)
admin.site.register(Storage)
admin.site.register(FolderObject)
admin.site.register(FileObject)
admin.site.register(PictureFileObject)
admin.site.register(MusicFileObject)