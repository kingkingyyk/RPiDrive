from django.core.management.base import BaseCommand, CommandError
from django.utils.timezone import get_current_timezone
from annoying.functions import get_object_or_None
from drive.models import Storage, FolderObject, FileObject, FileTypes, PictureFileObject, MusicFileObject, File, FolderObject
from threading import Thread
from queue import SimpleQueue
from datetime import datetime
from exif import Image
from ...mq.mq import MQUtils, MQChannels
from ...utils.file_utils import FileUtils
import os, time, eyed3, traceback, mimetypes, json
from django.db import transaction

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

    def update_folder(self, base_path, parent_folder, full_path):
        name = os.path.basename(full_path) if parent_folder else 'My Drive'
        rp = full_path[len(base_path)+1:]
        last_modified = datetime.fromtimestamp(os.path.getmtime(full_path), tz=get_current_timezone())

        obj = get_object_or_None(FolderObject, relative_path=rp)
        if not obj:
            obj = FolderObject(name=name, relative_path=rp,
                                parent_folder=parent_folder, 
                                last_modified=datetime.min)
        if obj.last_modified != last_modified:
            obj.last_modified = last_modified
            obj.save()

    def perform_index(self, base_path, start_folder):
        queue = SimpleQueue()
        queue.put(start_folder)
        while not queue.empty():
            curr_folder = queue.get()
            curr_folder_obj = FolderObject.objects.get(relative_path=curr_folder[len(base_path)+1:])
            
            for f in File.objects.filter(parent_folder=curr_folder_obj).all():
                fp = os.path.join(base_path, f.relative_path)
                if not os.path.exists(fp):
                    f.delete()

            for f in os.listdir(curr_folder):
                f_full_path = os.path.join(curr_folder, f)
                if os.path.isdir(f_full_path):
                    queue.put(f_full_path)
                    self.update_folder(base_path, curr_folder_obj, f_full_path)
                elif os.path.isfile(f_full_path):
                    self.update_file(base_path, curr_folder_obj, f_full_path)

    def update_file(self, base_path, parent_folder, full_path):
        name = os.path.basename(full_path)
        rp = full_path[len(base_path)+1:]
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

    @transaction.atomic
    def update_relative_path(self, base_path, parent_folder):
        queue = SimpleQueue()
        queue.put(parent_folder)

        while not queue.empty():
            curr_folder = queue.get()
            for f in File.objects.filter(parent_folder=curr_folder).all():
                rel_path = curr_folder.relative_path + os.path.sep if curr_folder.relative_path == '' else ''
                new_relative_path = rel_path + os.path.sep + f.name
                if f.relative_path != new_relative_path:
                    f.save()
                    if isinstance(f, FolderObject):
                        queue.put(f)


class FileOperator:

    @staticmethod
    def start():
        MQUtils.subscribe_channel(MQChannels.FOLDER_OBJ_TO_CREATE, FileOperator.folder_to_create)
        MQUtils.subscribe_channel(MQChannels.FILE_TO_DELETE, FileOperator.file_to_delete)
        MQUtils.subscribe_channel(MQChannels.FILE_TO_RENAME, FileOperator.file_to_rename)
        MQUtils.subscribe_channel(MQChannels.FILE_TO_MOVE, FileOperator.file_to_move)

    @staticmethod
    def folder_to_create(channel, method_frame, header_frame, body):
        try:
            data = json.loads(body)
            storage = Storage.objects.get(primary=True)
            parent_folder = FolderObject.objects.get(pk=data['message']['folder'])
            fp = os.path.join(storage.base_path, parent_folder.relative_path, data['message']['name'])
            os.mkdir(fp)
            Indexer().update_folder(storage.base_path, parent_folder, fp)
        except:
            print(traceback.format_exc())
        MQUtils.push_to_channel(data['reply-queue'],'{}',False)
        channel.basic_ack(delivery_tag=method_frame.delivery_tag)

    @staticmethod
    def file_to_delete(channel, method_frame, header_frame, body):
        data = json.loads(body)
        storage = Storage.objects.get(primary=True)
        for fileId in data['message']['files']:
            try:
                f = File.objects.get(pk=fileId)
                FileUtils.delete_file_or_dir(os.path.join(storage.base_path, f.relative_path))
                f.delete()
            except:
                print(traceback.format_exc())
        MQUtils.push_to_channel(data['reply-queue'],'{}',False)
        channel.basic_ack(delivery_tag=method_frame.delivery_tag)

    @staticmethod
    def file_to_rename(channel, method_frame, header_frame, body):
        def update_rel_path(base_path, folder):
            Indexer().update_relative_path(storage.base_path, folder)
        
        data = json.loads(body)
        storage = Storage.objects.get(primary=True)
        file = File.objects.select_related('parent_folder').get(pk=data['message']['file'])
        new_name = data['message']['name']
        try:
            os.rename(os.path.join(storage.base_path, file.relative_path), os.path.join(storage.base_path, file.parent_folder.relative_path ,new_name))
            file.relative_path = file.relative_path[:-len(file.name)] + new_name
            file.name = new_name
            file.save()
            if isinstance(file, FolderObject):
                Thread(target=update_rel_path, args=(storage.base_path, file)).start()
        except:
            print(traceback.format_exc())
        MQUtils.push_to_channel(data['reply-queue'],'{}',False)
        channel.basic_ack(delivery_tag=method_frame.delivery_tag)

    @staticmethod
    def file_to_move(channel, method_frame, header_frame, body):
        def update_rel_path(base_path, folder):
            Indexer().update_relative_path(storage.base_path, folder)

        data = json.loads(body)
        storage = Storage.objects.get(primary=True)
        folder = FolderObject.objects.get(pk=data['message']['folder'])
        for fileId in data['message']['files']:
            try:
                f = File.objects.get(pk=fileId)
                old_path = os.path.join(storage.base_path, f.relative_path)
                new_path = os.path.join(storage.base_path, folder.relative_path, f.name)

                postfix_count = 1;
                while os.path.exists(new_path):
                    fname_split = f.name.split('.')
                    print(fname_split)
                    if len(fname_split) == 1:
                        fname_split[-1] = fname_split[-1] + '_' + str(postfix_count)
                    else:
                        fname_split[-2] = fname_split[-2] + '_' + str(postfix_count)
                    new_fname = '.'.join(fname_split)
                    new_path = os.path.join(storage.base_path, folder.relative_path, new_fname)
                    postfix_count += 1
                
                os.rename(old_path, new_path)
                f.relative_path = new_path[len(storage.base_path)+1:]
                f.name = os.path.basename(new_path)
                f.parent_folder = folder
                f.save()
            except:
                print(traceback.format_exc())
        Thread(target=update_rel_path, args=(storage.base_path, folder)).start()

        MQUtils.push_to_channel(data['reply-queue'],'{}',False)
        channel.basic_ack(delivery_tag=method_frame.delivery_tag)