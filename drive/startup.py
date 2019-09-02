from threading import Thread
from .models import *
from .views import get_storage
from .downloader import DownloaderStatus
import time, sys, requests


def downloader_loop():
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
            with open(real_path, 'ab') as file_obj:
                headers = {}
                pos = file_obj.tell()
                if pos:
                    headers['Range'] = f'bytes={pos}-'
                response = requests.get(download_to_do.source_url, headers=headers,
                                        verify=False, stream=True,
                                        auth=(download_to_do.username, download_to_do.password))
                if response.status_code < 300:
                    download_to_do.status = DownloadStatus.downloading.value
                    download_to_do.save()
                    total_size = int(response.headers.get('Content-Length'))
                    DownloaderStatus.download_progress[download_to_do.id] = (float(pos) / total_size) * 100;
                    for data in response.iter_content(chunk_size=1024):
                        file_obj.write(data)
                        pos += 1024
                        DownloaderStatus.download_progress[download_to_do.id] = (float(pos) / total_size) * 100;
                    DownloaderStatus.download_progress.pop(download_to_do.id)

                    download_to_do.status = DownloadStatus.finished.value
                else:
                    download_to_do.status = DownloadStatus.error.value

                download_to_do.file.size=os.path.getsize(real_path)
                download_to_do.save()
        time.sleep(5)


def start_downloader():
    t = Thread(target=downloader_loop)
    t.daemon = True
    t.start()


def first_time_setup():
    if sys.argv[1] == 'runserver':
        try:
            drive = Drive.objects.first()
            if drive is None:
                drive = Drive(name='RPi Drive')
                drive.save()
        except:
            from django.core.management import execute_from_command_line
            execute_from_command_line(['', 'makemigrations', 'drive'])
            execute_from_command_line(['', 'migrate', 'drive'])
            execute_from_command_line(['', 'runserver'])


def initialize_startup():
    first_time_setup()
    start_downloader()