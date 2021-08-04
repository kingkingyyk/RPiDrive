FROM registry.gitlab.com/kingkingyyk/rpidrive:lib-1.0.0

ADD build.tar.gz /

WORKDIR /app

ENV MODE=standalone

RUN chmod +x start.sh &&\
    apt update && \
    apt install gcc libpq-dev g++ libffi-dev make -y && \
    pip install --no-cache-dir -r requirements.txt && \
    apt purge -y --autoremove -o APT::AutoRemove::RecommendsImportant=false gcc g++ make && \
    rm -rf /var/lib/apt/lists/*

EXPOSE 8000

CMD "/app/start.sh"
