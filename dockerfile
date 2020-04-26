FROM python:slim

COPY backend /mnt
RUN chmod 777 /mnt/docker-start.sh &&\
    apt update && \
    apt install gcc libpq-dev -y && \
    pip install --no-cache-dir -r /mnt/requirements.txt && \
    apt purge -y --autoremove -o APT::AutoRemove::RecommendsImportant=false gcc && \
    rm -rf /var/lib/apt/lists/*

EXPOSE 8888
ENV DJANGO_SETTINGS_MODULE RPiDrive_ng.settings.prod

CMD "/mnt/docker-start.sh"