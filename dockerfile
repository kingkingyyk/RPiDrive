FROM python:slim

COPY backend /mnt
RUN apt update && \
    apt install gcc libpq-dev -y && \
    pip install --no-cache-dir -r /mnt/requirements.txt && \
    apt purge -y --autoremove -o APT::AutoRemove::RecommendsImportant=false libpq-dev gcc && \
    rm -rf /var/lib/apt/lists/*

EXPOSE 8080
ENV DJANGO_SETTINGS_MODULE RPiDrive_ng.settings.prod

CMD ["gunicorn", "-w", "9", "-b" "0.0.0.0:8888", "RPiDrive_ng.wsgi", "--timeout", "3000", "--preload"]