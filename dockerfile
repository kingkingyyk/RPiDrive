FROM registry.gitlab.com/kingkingyyk/rpidrive:lib-1.0.0

ADD build.tar.gz /

WORKDIR /app

ENV MODE=web

RUN chmod +x start.sh &&\
    pip install --no-cache-dir -r requirements.txt

EXPOSE 8000

ENTRYPOINT ["/bin/bash"]
CMD ["/app/start.sh"]
