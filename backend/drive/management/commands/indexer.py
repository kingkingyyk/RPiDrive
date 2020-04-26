import json
import mimetypes
import os
import time
import traceback
from datetime import datetime
from queue import SimpleQueue
from threading import Thread

import eyed3
from annoying.functions import get_object_or_None
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils.timezone import get_current_timezone
from exif import Image

from drive.models import (File, FileObject, FileTypes, FolderObject,
                          MusicFileObject, PictureFileObject, Storage)
from drive.utils.file_utils import FileUtils


class Command(BaseCommand):
    help = 'Run indexer service'

    def handle(self, *args, **options):
        print('Performing file indexing')
        Indexer.perform_full_index()
        print('Done')

class Indexer:

    @staticmethod
    def perform_full_index():
        with transaction.atomic():
            storage = Storage.objects.get(primary=True)
            Indexer.update_folder(storage.base_path, None, storage.base_path)
            Indexer.perform_index(storage.base_path, storage.base_path)

    @staticmethod
    def update_folder(base_path, parent_folder, full_path):
        name = os.path.basename(full_path) if parent_folder else 'My Drive'
        rp = '' if base_path == full_path else full_path[len(base_path)+1:]
        last_modified = datetime.fromtimestamp(
            os.path.getmtime(full_path), tz=get_current_timezone())

        with transaction.atomic():
            obj = get_object_or_None(FolderObject.objects.select_for_update(), relative_path=rp)
            if not obj:
                obj = FolderObject(name=name, relative_path=rp,
                                parent_folder=parent_folder,
                                last_modified=datetime.min)
            if obj.last_modified != last_modified:
                obj.last_modified = last_modified
                obj.save()

    @staticmethod
    def perform_index(base_path, start_folder):
        with transaction.atomic():
            queue = SimpleQueue()
            queue.put(start_folder)
            while not queue.empty():
                curr_folder = queue.get()
                curr_folder_rp = '' if base_path == curr_folder else curr_folder[len(base_path)+1:]
                curr_folder_obj = FolderObject.objects.get(
                    relative_path=curr_folder_rp)

                for f in File.objects.filter(parent_folder=curr_folder_obj).all():
                    fp = os.path.join(base_path, f.relative_path)
                    if not os.path.exists(fp):
                        if isinstance(f, FolderObject):
                            Indexer.recurse_delete(f)
                        f.delete()

                for f in os.listdir(curr_folder):
                    f_full_path = os.path.join(curr_folder, f)
                    if os.path.isdir(f_full_path):
                        queue.put(f_full_path)
                        Indexer.update_folder(base_path, curr_folder_obj, f_full_path)
                    elif os.path.isfile(f_full_path):
                        Indexer.update_file(base_path, curr_folder_obj, f_full_path)
    
    @staticmethod
    def recurse_delete(folder_obj):
        for f in File.objects.filter(parent_folder=folder_obj).all():
            if isinstance(f, FolderObject):
                Indexer.recurse_delete(f)
            f.delete()

    @staticmethod
    def update_file(base_path, parent_folder, full_path):
        name = os.path.basename(full_path)
        rp = full_path[len(base_path)+1:]
        last_modified = datetime.fromtimestamp(
            os.path.getmtime(full_path), tz=get_current_timezone())
        size = os.path.getsize(full_path)

        obj = get_object_or_None(File, relative_path=rp)
        if not obj:
            content_type = mimetypes.guess_type(
                full_path)[0] or 'application/octet-stream'

        file_type = FileTypes.get_type(full_path)
        if file_type == FileTypes.PICTURE:
            if not obj:
                obj = PictureFileObject(name=name, relative_path=rp,
                                        parent_folder=parent_folder,
                                        last_modified=datetime.min, size=0,
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
                        obj.title = audiofile.tag.title
                    else:
                        obj.title = '.'.join(name.split('.')[:-1])
                    if audiofile.tag.artist:
                        obj.artist = audiofile.tag.artist
                    if audiofile.tag.album:
                        obj.album = audiofile.tag.album
                    if audiofile.tag.genre:
                        obj.genre = audiofile.tag.genre
                except:
                    if not obj.title:
                        obj.title = '.'.join(name.split('.')[:-1])
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

    @staticmethod
    def update_relative_path(base_path, parent_folder):
        queue = SimpleQueue()
        queue.put(parent_folder)

        while not queue.empty():
            curr_folder = queue.get()
            for f in File.objects.select_for_update().filter(parent_folder=curr_folder).all():
                rel_path = curr_folder.relative_path + \
                    os.path.sep if curr_folder.relative_path == '' else ''
                new_relative_path = rel_path + os.path.sep + f.name
                if f.relative_path != new_relative_path:
                    f.save()
                    if isinstance(f, FolderObject):
                        queue.put(f)
