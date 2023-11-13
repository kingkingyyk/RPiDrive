from django.contrib import admin

from rpidrive.models import (
    Activity,
    File,
    Job,
    Playlist,
    PlaylistFile,
    PublicFileLink,
    Volume,
    VolumeUser,
)

admin.site.register(Activity)
admin.site.register(File)
admin.site.register(Job)
admin.site.register(Playlist)
admin.site.register(PlaylistFile)
admin.site.register(PublicFileLink)
admin.site.register(Volume)
admin.site.register(VolumeUser)
