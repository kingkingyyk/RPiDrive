from ..models import *
from threading import Thread
import os
import json
import logging
import traceback
import epub_meta
from tinytag import TinyTag
from exif import Image
from PyPDF2 import PdfFileReader
from mobi import Mobi


class InvalidStorageProviderTypeException(Exception):
    pass


class LocalStorageProviderIndexer:
    LOGGER = logging.getLogger(__name__)
    class FSFileObj:
        def __init__(self, name, path):
            self.name = name
            self.path = path
            self.children = []

    @staticmethod
    def sync(root: LocalFileObject, background=False):
        if background:
            Thread(target=LocalStorageProviderIndexer.sync_helper,
                   args=(root,)).start()
        else:
            LocalStorageProviderIndexer.sync_helper(root)

    @staticmethod
    def sync_helper(root: LocalFileObject):
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
        except:
            print(traceback.format_exc())
        StorageProvider.objects.filter(pk=root.storage_provider.pk).update(indexing=False)
        LocalStorageProviderIndexer.LOGGER.debug('Indexing done')

    @staticmethod
    def _construct_fs_tree(storage_provider: StorageProvider):
        root = LocalStorageProviderIndexer.FSFileObj(
            'ROOT', storage_provider.path)
        stk = [root]
        while stk:
            curr_parent = stk.pop()
            for fn in os.listdir(curr_parent.path):
                fp = os.path.join(curr_parent.path, fn)
                fobj = LocalStorageProviderIndexer.FSFileObj(fn, fp)
                curr_parent.children.append(fobj)
                if os.path.isdir(fp):
                    stk.append(fobj)
        return root

    @staticmethod
    def _construct_db_tree(root: LocalFileObject):
        return root

    @staticmethod
    def _sync_trees(fs_root, db_root):
        fs_stk = [fs_root]
        db_stk = [db_root]

        for fo in LocalFileObject.objects.filter(storage_provider=db_root.storage_provider).all():
            if not os.path.exists(fo.full_path):
                fo.delete()

        while fs_stk:
            fs = fs_stk.pop()
            db = db_stk.pop()

            fs_files = set(os.listdir(fs.path))
            db_files = set(x for x in LocalFileObject.objects.filter(
                parent__pk=db.pk).values_list('name', flat=True))

            new_fs_files = fs_files - db_files

            for f in fs_files:
                fp = os.path.join(fs.path, f)
                db_obj = None
                if f in new_fs_files:
                    LocalStorageProviderIndexer.LOGGER.debug('Indexing path {}'.format(fp))
                    db_obj = LocalFileObject.objects.create(name=f,
                                                            obj_type=FileObjectType.FOLDER if os.path.isdir(
                                                                fp) else FileObjectType.FILE,
                                                            parent=db,
                                                            storage_provider=db.storage_provider,
                                                            rel_path=fp[len(fs_root.path)+1:])
                if os.path.isdir(fp):
                    if not db_obj:
                        db_obj = LocalFileObject.objects.get(name=f,
                                                             obj_type=FileObjectType.FOLDER,
                                                             parent=db)
                    fs_stk.append(next(x for x in fs.children if x.name == f))
                    db_stk.append(db_obj)


class Metadata:

    @staticmethod
    def extract(file: LocalFileObject):
        data = {}
        if file.type in [FileExt.TYPE_MUSIC, FileExt.TYPE_MOVIE]:
            try:
                tags = TinyTag.get(file.full_path, image=True)
                data = json.loads(str(tags))
            except:
                print(traceback.format_exc())
        elif file.type == FileExt.TYPE_PICTURE:
            try:
                with open(file.full_path, 'rb') as fh:
                    img = Image(fh)
                if img.has_exif:
                    data = {key: img[key] for key in dir(img)}
            except:
                print(traceback.format_exc())
        elif file.type == FileExt.TYPE_BOOK:
            if file.extension == 'pdf':
                try:
                    with open(file.full_path, 'rb') as fh:
                        data = PdfFileReader(fh).getDocumentInfo()
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
        data = {}
        if file.type == FileExt.TYPE_MUSIC:
            return TinyTag.get(file.full_path, image=True).get_image()
        else:
            return b''
