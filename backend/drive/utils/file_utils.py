import os, shutil, stat


class FileUtils:

    @staticmethod
    def delete_dir(top, delete_root=True, best_effort=False):
        if os.path.exists(top):
            # Unlink symbolic linked files/folders
            for root, dirs, files in os.walk(top, topdown=False):
                for name in [x for x in files + dirs if os.path.islink(os.path.join(root, x))]:
                    os.unlink(os.path.join(root, name))

            for root, dirs, files in os.walk(top, topdown=False):
                for name in files:
                    FileUtils.delete_file_or_dir(os.path.join(root, name), best_effort)
                for name in dirs:
                    FileUtils.delete_file_or_dir(os.path.join(root, name), best_effort)

            if delete_root:
                FileUtils.delete_file_or_dir(top, best_effort)

    @staticmethod
    def delete_file_or_dir(top, best_effort=False):
        if os.path.exists(top):
            if os.path.islink(top):
                if best_effort:
                    try:
                        os.unlink(top)
                    except:
                        pass
                else:
                    os.unlink(top)

        if os.path.exists(top):
            if os.path.isfile(top):
                if best_effort:
                    try:
                        os.chmod(top, stat.S_IWRITE)
                        os.remove(top)
                    except:
                        pass
                else:
                    os.chmod(top, stat.S_IWRITE)
                    os.remove(top)
            else:
                shutil.rmtree(top, ignore_errors=best_effort)