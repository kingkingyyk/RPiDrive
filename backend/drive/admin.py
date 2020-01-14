from django.contrib import admin
from .models import *

# Register your models here.
admin.site.register(Drive)
admin.site.register(Storage)
admin.site.register(Folder)
admin.site.register(File)
admin.site.register(Permission)
admin.site.register(Download)