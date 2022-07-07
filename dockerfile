FROM python:3.10-slim-bullseye

ADD build.tar.gz /

WORKDIR /app

ENV MODE=web

RUN chmod +x start.sh &&\
    apt update &&\
    apt install gcc libpq-dev g++ libffi-dev make -y &&\
    pip install --no-cache-dir -r requirements.txt &&\
    rm -rf /var/lib/apt/lists/*

EXPOSE 8000

ENTRYPOINT ["/bin/bash"]
CMD ["/app/start.sh"]
