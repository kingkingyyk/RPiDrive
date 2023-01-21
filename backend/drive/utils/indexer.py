import json
import logging
import os
import traceback

from datetime import datetime
from typing import Dict

import epub_meta

from django.utils import timezone
from tinytag import TinyTag
from exif import Image
from mobi import Mobi
from PyPDF2 import PdfFileReader
from drive.models import (
    FileExt,
    FileObjectTypeEnum,
    LocalFileObject,
    StorageProvider,
    StorageProviderTypeEnum,
)

class InvalidStorageProviderTypeException(Exception):
    """InvalidStorageProviderTypeException"""

class LocalStorageProviderIndexer:
    """LocalStorageProviderIndexer"""
    _ATTRS_UPDATE = ['last_modified', 'size']

    class FSFileObj:
        """FSFileObj"""
        def __init__(self, name, path):
            self.name = name
            self.path = path
            self.children = []

    @staticmethod
    def _get_attr_values(f_p: str) -> Dict:
        return {
            'last_modified': datetime.fromtimestamp(
                os.path.getmtime(f_p), tz=timezone.get_current_timezone()),
            'size': os.path.getsize(f_p)
        }

    @staticmethod
    def _sync_attrs(file_obj: LocalFileObject):
        attr_values = (
            LocalStorageProviderIndexer
            ._get_attr_values(file_obj.full_path)
        )
        attr_update = []
        for attr in LocalStorageProviderIndexer._ATTRS_UPDATE:
            if attr_values[attr] != getattr(file_obj, attr):
                setattr(file_obj, attr, attr_values[attr])
                attr_update.append(attr)
        if attr_update:
            file_obj.save(update_fields=attr_update)

    @staticmethod
    def sync(root: LocalFileObject):
        """Perform LocalFileObject and file system sync"""
        logging.info('Indexing started')
        LocalStorageProviderIndexer._sync_attrs(root)
        storage_provider = root.storage_provider
        if not storage_provider.indexing:
            storage_provider.indexing = True
            storage_provider.save(update_fields=['indexing'])

        if storage_provider.type != StorageProviderTypeEnum.LOCAL_PATH:
            raise InvalidStorageProviderTypeException()
        try:
            fs_tree = LocalStorageProviderIndexer._construct_fs_tree(
                storage_provider)
            db_tree = LocalStorageProviderIndexer._construct_db_tree(root)
            LocalStorageProviderIndexer._sync_trees(fs_tree, db_tree)
        except: # pylint: disable=bare-except
            print(traceback.format_exc())

        storage_provider.indexing = False
        storage_provider.last_indexed = timezone.now()
        storage_provider.save(update_fields=['indexing', 'last_indexed'])
        logging.info('Indexing done')

    @staticmethod
    def _construct_fs_tree(storage_provider: StorageProvider):
        root = LocalStorageProviderIndexer.FSFileObj(
            'ROOT', storage_provider.path)
        stack = [root]
        while stack:
            curr_parent = stack.pop()
            for filename in os.listdir(curr_parent.path):
                file_path = os.path.join(curr_parent.path, filename)
                fobj = LocalStorageProviderIndexer.FSFileObj(
                    filename, file_path)
                curr_parent.children.append(fobj)
                if os.path.isdir(file_path):
                    stack.append(fobj)
        return root

    @staticmethod
    def _construct_db_tree(root: LocalFileObject):
        return root

    @staticmethod
    def _sync_trees(fs_root: str, db_root: LocalFileObject): # pylint: disable=too-many-locals
        fs_stk = [fs_root]
        db_stk = [db_root]

        for file_obj in LocalFileObject.objects.filter(
            storage_provider=db_root.storage_provider).all():
            if not os.path.exists(file_obj.full_path):
                file_obj.delete()

        while fs_stk:
            f_s = fs_stk.pop()
            d_b = db_stk.pop()

            fs_files = set(os.listdir(f_s.path))
            db_files = {x.name: x for x in LocalFileObject.objects.filter(
                parent__pk=d_b.pk).all()}

            new_fs_files = fs_files - db_files.keys()

            for file in fs_files:
                f_p = os.path.join(f_s.path, file)
                db_obj = None

                if file in new_fs_files:
                    logging.debug('Indexing path %s', f_p)
                    db_obj = LocalFileObject.objects.create(
                        name=file,
                        obj_type=FileObjectTypeEnum.FOLDER if os.path.isdir(
                            f_p) else FileObjectTypeEnum.FILE,
                        parent=d_b,
                        storage_provider=d_b.storage_provider,
                        rel_path=f_p[len(fs_root.path)+1:],
                        **LocalStorageProviderIndexer._get_attr_values(
                            f_p),
                    )
                else:
                    LocalStorageProviderIndexer._sync_attrs(db_files[file])
                if os.path.isdir(f_p):
                    if not db_obj:
                        db_obj = LocalFileObject.objects.get(
                            name=file,
                            obj_type=FileObjectTypeEnum.FOLDER,
                            parent=d_b
                        )
                    fs_stk.append(next(x for x in f_s.children if x.name == file))
                    db_stk.append(db_obj)


class Metadata:
    """File Metadata"""

    # pylint: disable=bare-except
    @staticmethod
    def extract(file: LocalFileObject):
        """Extract metadata from file"""
        data = {}
        if file.type in [FileExt.TYPE_MUSIC, FileExt.TYPE_MOVIE]:
            try:
                tags = TinyTag.get(file.full_path, image=True)
                data = json.loads(str(tags))
            except:
                print(traceback.format_exc())
        elif file.type == FileExt.TYPE_PICTURE:
            try:
                with open(file.full_path, 'rb') as f_h:
                    img = Image(f_h)
                if img.has_exif:
                    data = {key: img[key] for key in dir(img)}
            except:
                print(traceback.format_exc())
        elif file.type == FileExt.TYPE_BOOK:
            if file.extension == 'pdf':
                try:
                    with open(file.full_path, 'rb') as f_h:
                        data = PdfFileReader(f_h).getDocumentInfo()
                except:
                    print(traceback.format_exc())
            elif file.extension == 'epub':
                try:
                    data = epub_meta.get_epub_metadata(
                        file.full_path, read_cover_image=True)
                except:
                    print(traceback.format_exc())
            elif file.extesion == 'mobi':
                try:
                    data = Mobi(file.full_path).parse().config
                except:
                    print(traceback.format_exc())
        return data

    @staticmethod
    def get_album_image(file: LocalFileObject) -> bytes:
        """Extract album image from file"""
        if file.type == FileExt.TYPE_MUSIC:
            return TinyTag.get(file.full_path, image=True).get_image()
        return b''
