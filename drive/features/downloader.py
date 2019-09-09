import urllib3
from threading import Thread
from drive.models import *
from django.conf import settings
from django.db import transaction
from requests import Timeout
from drive.utils.file_utils import FileUtils
from drive.utils.model_utils import ModelUtils
import time, requests, humanize


urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

downloader_thread = None


class DownloaderStatus:
    download_progress = {}


class StopException(Exception):
    pass


class Downloader:

    @staticmethod
    def downloader_loop():
        while True:
            download_to_do = Download.objects\
                            .filter(status=DownloadStatus.downloading.value)\
                            .select_related('file')\
                            .order_by('file__last_modified').first()
            if not download_to_do:
                download_to_do = Download.objects\
                                .filter(status=DownloadStatus.queue.value)\
                                .select_related('file')\
                                .order_by('file__last_modified').first()
            if download_to_do:
                real_path = os.path.join(ModelUtils.get_storage().base_path,download_to_do.file.relative_path)
                has_error = True
                force_stop = False
                detailed_status = None

                try:
                    with open(real_path, 'ab') as file_obj:
                        headers = {}
                        pos = file_obj.tell()
                        if pos:
                            headers['Range'] = f'bytes={pos}-'
                        response = requests.get(download_to_do.source_url, headers=headers,
                                                verify=False, stream=True, allow_redirects=True,
                                                auth=(download_to_do.username, download_to_do.password),
                                                timeout=(settings.DOWNLOADER_CONNECT_TIMEOUT, settings.DOWNLOADER_READ_TIMEOUT))
                        if response.status_code < 400:
                            download_to_do.status = DownloadStatus.downloading.value
                            download_to_do.save()
                            receiving_size = int(response.headers.get('Content-Length'))
                            initial_size = pos
                            curr_downloaded_size = 0
                            start_time = datetime.now()

                            DownloaderStatus.download_progress[download_to_do.id] = (float(pos) / (initial_size + receiving_size)) * 100;

                            try:
                                for data in response.iter_content(chunk_size=1024):
                                    file_obj.write(data)
                                    curr_downloaded_size += len(data)
                                    pos += len(data)
                                    time_diff = max((datetime.now()-start_time).seconds, 1)
                                    DownloaderStatus.download_progress[download_to_do.id] = "{:.2f}% ({}/s)".format((float(pos) / (initial_size + receiving_size)) * 100, humanize.naturalsize(int(curr_downloaded_size/time_diff)))

                                    if Download.objects.get(id=download_to_do.id).to_stop:
                                        force_stop = True
                                        raise StopException()
                            except StopException:
                                pass

                            DownloaderStatus.download_progress.pop(download_to_do.id)
                            download_to_do.status = DownloadStatus.stopped.value if force_stop else DownloadStatus.finished.value
                            has_error = False
                except IOError as e:
                    detailed_status = 'IOError : ' + str(e)
                except Timeout:
                    detailed_status = 'Request timed out when requesting data from ' + download_to_do.source_url

                download_to_do = Download.objects.get(id=download_to_do.id)
                if detailed_status:
                    download_to_do.detailed_status = detailed_status

                if has_error:
                    download_to_do.status = DownloadStatus.error.value

                if download_to_do.to_delete_file:
                    for i in range(0, 3):
                        end = False
                        if os.path.exists(real_path):
                            try:
                                FileUtils.delete_file_or_dir(real_path)
                                end = True
                            except:
                                pass
                        if not end:
                            break
                        else:
                            time.sleep(1)
                    download_to_do.file.delete()
                else:
                    download_to_do.save()
            time.sleep(5)

    @staticmethod
    def onstart_cleanup():
        downloads_to_clear = Download.objects.filter(to_delete_file=True).select_related('file').all()
        for download in downloads_to_clear:
            FileUtils.delete_file_or_dir(os.path.join(ModelUtils.get_storage().base_path, download.file.relative_path))
            download.file.delete()

    @staticmethod
    @transaction.atomic
    def start():
        time = datetime.now(tz=get_current_timezone())
        drive = Drive.objects.get()
        if drive.downloader_start - time > timedelta(seconds=3):
            drive.downloader_start = time
            drive.save()

            global downloader_thread
            Downloader.onstart_cleanup()

            downloader_thread = Thread(target=Downloader.downloader_loop)
            downloader_thread.daemon = True
            downloader_thread.start()

    @staticmethod
    def interrupt(download):
        if not download.to_stop:
            download.to_stop = True
            download.to_delete_file = True
            download.status = DownloadStatus.stopped.value
            download.save()
