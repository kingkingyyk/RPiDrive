from drive.models import *
from django.contrib.auth.models import User

# Create your models here.
class Playlist(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.TextField(db_index=True)

class FileInPlaylist(models.Model):
    file = models.ForeignKey(FileObject, on_delete=models.CASCADE)
    playlist = models.ForeignKey(Playlist, on_delete=models.CASCADE)
    index = models.IntegerField()