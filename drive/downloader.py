import urllib3
from threading import Thread
from .models import *
from django.conf import settings
from requests import Timeout
from .utils import FileUtils
import time, requests


urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

downloader_thread = None


class DownloaderStatus:
    download_progress = {}


class Downloader:

    @staticmethod
    def downloader_loop():
        from .views import get_storage

        while True:
            download_to_do = Download.objects\
                            .filter(status=DownloadStatus.downloading.value)\
                            .select_related('file')\
                            .order_by('file__last_modified').first()
            if download_to_do is None:
                download_to_do = Download.objects\
                                .filter(status=DownloadStatus.queue.value)\
                                .select_related('file')\
                                .order_by('file__last_modified').first()

            if download_to_do is not None:
                real_path = os.path.join(get_storage().base_path,download_to_do.file.relative_path)
                has_error = True
                force_stop = False

                try:
                    with open(real_path, 'ab') as file_obj:
                        headers = {}
                        pos = file_obj.tell()
                        if pos:
                            headers['Range'] = f'bytes={pos}-'

                            response = requests.get(download_to_do.source_url, headers=headers,
                                                    verify=False, stream=True,
                                                    auth=(download_to_do.username, download_to_do.password),
                                                    timeout=(settings.DOWNLOADER_CONNECT_TIMEOUT, settings.DOWNLOADER_READ_TIMEOUT))
                            if response.status_code < 300:
                                download_to_do.status = DownloadStatus.downloading.value
                                download_to_do.save()
                                receiving_size = int(response.headers.get('Content-Length'))
                                initial_size = pos
                                DownloaderStatus.download_progress[download_to_do.id] = (float(pos) / (initial_size + receiving_size)) * 100;
                                for data in response.iter_content(chunk_size=1024):
                                    file_obj.write(data)
                                    pos += 1024
                                    DownloaderStatus.download_progress[download_to_do.id] = (float(pos) / (initial_size + receiving_size)) * 100;

                                    if download_to_do.to_stop:
                                        force_stop = True
                                        break

                                DownloaderStatus.download_progress.pop(download_to_do.id)
                                download_to_do.status = DownloaderStatus.stopped.value if force_stop else DownloadStatus.finished.value
                    has_error = False
                except IOError as e:
                    download_to_do.detailed_status = 'IOError : ' - str(e)
                except Timeout:
                    download_to_do.detailed_status = 'Request timed out when requesting data from ' + download_to_do.source_url

                if has_error:
                    download_to_do.status = DownloadStatus.error.value
                else:
                    download_to_do.file.size = os.path.getsize(real_path)

                if download_to_do.to_delete_file:
                    FileUtils.delete_file_or_dir(real_path)
                    download_to_do.f.delete()
                else:
                    download_to_do.save()
            time.sleep(5)

    @staticmethod
    def start():
        global downloader_thread
        downloader_thread = Thread(target=Downloader.downloader_loop)
        downloader_thread.daemon = True
        downloader_thread.start()

    @staticmethod
    def interrupt(download):
        download.to_stop = DownloaderStatus.stopped.value
        if DownloaderStatus.download_progress.get(download.id, None):
            download.to_delete_file = True
        download.save()