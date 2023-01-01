from django.contrib import admin
from .models import (
    FileObjectAlias,
    LocalFileObject,
    Job,
    StorageProvider,
    System,
)

admin.site.register(FileObjectAlias)
admin.site.register(Job)
admin.site.register(LocalFileObject)
admin.site.register(StorageProvider)
admin.site.register(System)
