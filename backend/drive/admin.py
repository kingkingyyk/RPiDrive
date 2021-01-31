from django.contrib import admin
from .models import *

# Register your models here.
admin.site.register(StorageProvider)
admin.site.register(LocalFileObject)
admin.site.register(System)