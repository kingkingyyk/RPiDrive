FROM python:3.12-slim-bookworm

ADD backend /app

WORKDIR /app

RUN chmod +x start.sh &&\
    apt update &&\
    apt install gcc libpq-dev g++ libffi-dev make mime-support -y &&\
    pip install --no-cache-dir -r .req/build-multiarch.txt &&\
    rm -rf /var/lib/apt/lists/*

ENV MODE=web \
    RPIDRIVE_DATA_DIR=/app/.config \
    RPIDRIVE_LOG_DIR=/app/logs \
    DJANGO_SETTINGS_MODULE=backend.settings.prod

EXPOSE 8000

CMD ["bash", "start.sh"]
