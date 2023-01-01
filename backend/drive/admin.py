from django.contrib import admin
from .models import (
    LocalFileObject,
    Job,
    StorageProvider,
    System,
)

# Register your models here.
admin.site.register(Job)
admin.site.register(LocalFileObject)
admin.site.register(StorageProvider)
admin.site.register(System)
