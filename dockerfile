FROM python:slim-buster
ENV DJANGO_SETTINGS_MODULE RPiDrive_ng.settings.prod

COPY backend /mnt
RUN pip install --no-cache-dir -r /mnt/requirements.txt

CMD ["gunicorn", "-w", "9", "-b" "0.0.0.0:8888", "RPiDrive_ng.wsgi", "--timeout", "3000", "--preload"]