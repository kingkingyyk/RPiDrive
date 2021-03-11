FROM python:3.9-slim-buster

ADD build.tar.gz /

WORKDIR /app

RUN chmod +x start.sh &&\
    apt update && \
    apt install gcc libpq-dev g++ libffi-dev -y && \
    pip install --no-cache-dir -r requirements.txt && \
    apt purge -y --autoremove -o APT::AutoRemove::RecommendsImportant=false gcc g++ && \
    rm -rf /var/lib/apt/lists/*

EXPOSE 8000

CMD "/app/start.sh"
