FROM python:3.9-slim-buster

ADD build.tar.gz /

WORKDIR /app

ENV MODE=web

RUN chmod +x start.sh &&\
    apt update &&\
    apt install libpq-dev libffi-dev -y &&\
    pip install --no-cache-dir -r requirements.txt

EXPOSE 8000

ENTRYPOINT ["/bin/bash"]
CMD ["/app/start.sh"]
