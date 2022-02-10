import json
import logging
import os
import traceback
import epub_meta
from tinytag import TinyTag
from exif import Image
from mobi import Mobi
from PyPDF2 import PdfFileReader
from django.utils import timezone
from drive.models import (
    FileExt,
    FileObjectType,
    LocalFileObject,
    StorageProvider,
    StorageProviderType,
)

class InvalidStorageProviderTypeException(Exception):
    """InvalidStorageProviderTypeException"""

class LocalStorageProviderIndexer:
    """LocalStorageProviderIndexer"""

    LOGGER = logging.getLogger(__name__)
    class FSFileObj:
        """FSFileObj"""
        def __init__(self, name, path):
            self.name = name
            self.path = path
            self.children = []

    @staticmethod
    def sync(root: LocalFileObject):
        """Perform LocalFileObject and file system sync"""
        LocalStorageProviderIndexer.LOGGER.debug('Indexing started')
        storage_provider = root.storage_provider
        StorageProvider.objects.filter(pk=root.storage_provider.pk).update(indexing=True)
        if storage_provider.type != StorageProviderType.LOCAL_PATH:
            raise InvalidStorageProviderTypeException()
        try:
            fs_tree = LocalStorageProviderIndexer._construct_fs_tree(
                storage_provider)
            db_tree = LocalStorageProviderIndexer._construct_db_tree(root)
            LocalStorageProviderIndexer._sync_trees(fs_tree, db_tree)
        except: # pylint: disable=bare-except
            print(traceback.format_exc())
        StorageProvider.objects.filter(
            pk=root.storage_provider.pk).update(
                indexing=False, last_indexed=timezone.now())
        LocalStorageProviderIndexer.LOGGER.debug('Indexing done')

    @staticmethod
    def _construct_fs_tree(storage_provider: StorageProvider):
        root = LocalStorageProviderIndexer.FSFileObj(
            'ROOT', storage_provider.path)
        stk = [root]
        while stk:
            curr_parent = stk.pop()
            for f_n in os.listdir(curr_parent.path):
                f_p = os.path.join(curr_parent.path, f_n)
                fobj = LocalStorageProviderIndexer.FSFileObj(f_n, f_p)
                curr_parent.children.append(fobj)
                if os.path.isdir(f_p):
                    stk.append(fobj)
        return root

    @staticmethod
    def _construct_db_tree(root: LocalFileObject):
        return root

    @staticmethod
    def _sync_trees(fs_root, db_root):
        fs_stk = [fs_root]
        db_stk = [db_root]

        for f_o in LocalFileObject.objects.filter(
            storage_provider=db_root.storage_provider).all():
            if not os.path.exists(f_o.full_path):
                f_o.delete()

        while fs_stk:
            f_s = fs_stk.pop()
            d_b = db_stk.pop()

            fs_files = set(os.listdir(f_s.path))
            db_files = set(x for x in LocalFileObject.objects.filter(
                parent__pk=d_b.pk).values_list('name', flat=True))

            new_fs_files = fs_files - db_files

            for file in fs_files:
                f_p = os.path.join(f_s.path, file)
                db_obj = None
                if file in new_fs_files:
                    LocalStorageProviderIndexer.LOGGER.debug('Indexing path %s', f_p)
                    db_obj = LocalFileObject.objects.create(
                        name=file,
                        obj_type=FileObjectType.FOLDER if os.path.isdir(
                            f_p) else FileObjectType.FILE,
                        parent=d_b,
                        storage_provider=d_b.storage_provider,
                        rel_path=f_p[len(fs_root.path)+1:])
                if os.path.isdir(f_p):
                    if not db_obj:
                        db_obj = LocalFileObject.objects.get(name=file,
                                                             obj_type=FileObjectType.FOLDER,
                                                             parent=d_b)
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
