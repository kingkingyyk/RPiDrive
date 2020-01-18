from django.core.management.base import BaseCommand, CommandError
from django.utils.timezone import get_current_timezone
from annoying.functions import get_object_or_None
from drive.models import Storage, FolderObject, FileObject, FileTypes, PictureFileObject, MusicFileObject, File
from threading import Thread
from queue import SimpleQueue
from datetime import datetime
from exif import Image
from ...mq.mq import MQUtils, MQChannels
import os, time, eyed3, traceback, mimetypes

class Command(BaseCommand):
    help = 'Run indexer service'

    def handle(self, *args, **options):
        Indexer().start()
        FileOperator.start()


class Indexer(Thread):

    def run(self):
        print('Performing initial sync...')
        self.perform_full_index()
        print('Initial Sync done!')

    def perform_full_index(self):
        storage = Storage.objects.get(primary=True)
        self.update_folder(storage.base_path, None, storage.base_path)
        self.perform_index(storage.base_path, storage.base_path)

    def perform_index(self, base_path, start_folder):
        queue = SimpleQueue()
        queue.put(start_folder)
        while not queue.empty():
            curr_folder = queue.get()
            curr_folder_obj = FolderObject.objects.get(relative_path=curr_folder[len(base_path):])
            
            for f in os.listdir(curr_folder):
                f_full_path = os.path.join(curr_folder, f)
                if os.path.isdir(f_full_path):
                    queue.put(f_full_path)
                    self.update_folder(base_path, curr_folder_obj, f_full_path)
                elif os.path.isfile(f_full_path):
                    self.update_file(base_path, curr_folder_obj, f_full_path)

    def update_folder(self, base_path, parent_folder, full_path):
        name = os.path.basename(full_path)
        rp = full_path[len(base_path):]
        last_modified = datetime.fromtimestamp(os.path.getmtime(full_path), tz=get_current_timezone())

        obj = get_object_or_None(FolderObject, relative_path=rp)
        if not obj:
            obj = FolderObject(name=name, relative_path=rp,
                                parent_folder=parent_folder, 
                                last_modified=datetime.min)
        if obj.last_modified != last_modified:
            obj.last_modified = last_modified
            obj.save()

    def update_file(self, base_path, parent_folder, full_path):
        name = os.path.basename(full_path)
        rp = full_path[len(base_path):]
        last_modified = datetime.fromtimestamp(os.path.getmtime(full_path), tz=get_current_timezone())
        size = os.path.getsize(full_path)

        obj = get_object_or_None(File, relative_path=rp)
        if not obj:
            content_type = mimetypes.guess_type(full_path)[0] or 'application/octet-stream'

        file_type = FileTypes.get_type(full_path)
        if file_type == FileTypes.PICTURE:
            if not obj:
                obj = PictureFileObject(name=name, relative_path=rp,
                                    parent_folder=parent_folder, 
                                    last_modified=datetime.min ,size=0,
                                    content_type=content_type)
                try:
                    with open(full_path, 'rb') as f:
                        img = Image(f)
                        exifs = dir(img)
                        if 'make' in exifs:
                            obj.body_make = img.make
                        if 'model' in exifs:
                            obj.body_model = img.model
                        if 'lens_make' in exifs:
                            obj.lens_make = img.lens_make
                        if 'lens_model' in exifs:
                            obj.lens_model = img.lens_model
                        if 'photographic_sensitivity' in exifs:
                            obj.iso = img.photographic_sensitivity
                        if 'aperture_value' in exifs:
                            obj.aperture = img.aperture_value
                        if 'shutter_speed_value' in exifs:
                            obj.shutter_speed = img.shutter_speed_value
                        if 'focal_length' in exifs:
                            obj.focal_length = img.focal_length
                except:
                    print(traceback.format_exc())
        elif file_type == FileTypes.MUSIC:
            if not obj:
                obj = MusicFileObject(name=name, relative_path=rp,
                                        parent_folder=parent_folder, 
                                        last_modified=datetime.min, size=0,
                                        content_type=content_type)
                try:
                    audiofile = eyed3.load(full_path)
                    if audiofile.tag.title:
                        obj.title =  audiofile.tag.title
                    else:
                        obj.title = '.'.join(name.split('.')[:-1])
                    if audiofile.tag.artist:
                        obj.artist = audiofile.tag.artist
                    if audiofile.tag.album:
                        obj.album = audiofile.tag.album
                    if audiofile.tag.genre:
                        obj.genre = audiofile.tag.genre
                except:
                    pass
        else:
            if not obj:
                obj = FileObject(name=name, relative_path=rp,
                                    parent_folder=parent_folder, 
                                    last_modified=datetime.min,
                                    size=0, content_type=content_type)

        if obj.last_modified != last_modified or obj.size != size:
            obj.last_modified = last_modified
            obj.size = size
            obj.save()


class FileOperator:

    @staticmethod
    def start():
        MQUtils.subscribe_channel(MQChannels.FOLDER_TO_CREATE, FileOperator.folder_to_create)

    @staticmethod
    def folder_to_create(channel, method_frame, header_frame, body):
        try:
            data = json.loads(body)
            storage = Storage.objects.get(primary=True).base_path
            parent_folder = Folder.objects.get(pk=data['message']['folder'])
            fp = os.path.join(storage, parent_folder.path[1:], data['message']['name'])
            Indexer().update_folder(storage.base_path, data['message']['folder'], fp)
            MQUtils.push_to_channel(data['reply-queue'],'',False)
        except:
            pass
        channel.basic_ack(delivery_tag=method_frame.delivery_tag)
