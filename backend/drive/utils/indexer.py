from ..models import *
import os
import logging


class InvalidStorageProviderTypeException(Exception):
    pass


class LocalStorageProviderIndexer:
    class FSFileObj:
        def __init__(self, name, path):
            self.name = name
            self.path = path
            self.children = []

    @staticmethod
    def sync(root: LocalFileObject):
        storage_provider = root.storage_provider
        if storage_provider.type != StorageProviderType.LOCAL_PATH:
            raise InvalidStorageProviderTypeException()
        fs_tree = LocalStorageProviderIndexer._construct_fs_tree(
            storage_provider)
        db_tree = LocalStorageProviderIndexer._construct_db_tree(root)
        LocalStorageProviderIndexer._sync_trees(fs_tree, db_tree)

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
        while fs_stk:
            fs = fs_stk.pop()
            db = db_stk.pop()

            fs_files = os.listdir(fs.path)
            db_files = LocalFileObject.objects.filter(parent__pk=db.pk).values_list('name', flat=True)

            delete_fs_files = [x for x in db_files if x not in fs_files]
            LocalFileObject.objects.filter(
                parent__pk=db.pk, name__in=delete_fs_files).delete()
            new_fs_files = [x for x in fs_files if x not in db_files]

            for f in new_fs_files:
                fp = os.path.join(fs.path, f)
                db_obj = LocalFileObject.objects.create(name=f,
                                                        obj_type=FileObjectType.FOLDER if os.path.isdir(
                                                            fp) else FileObjectType.FILE,
                                                        parent=db, storage_provider=db.storage_provider,
                                                        rel_path=fp[len(fs_root.path)+1:])
                if os.path.isdir(fp):
                    fs_stk.append(next(x for x in fs.children if x.name == f))
                    db_stk.append(db_obj)
