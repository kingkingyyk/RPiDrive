#!/bin/bash

if [ "$MODE" == "web" ]; then
    python manage.py makemigrations --noinput && \
    python manage.py migrate && \
    python manage.py makemigrations drive --noinput && \
    python manage.py migrate drive && \

    gunicorn rpidrive.wsgi
fi

if [ "$MODE" == "core" ]; then
    python manage.py makemigrations --noinput && \
    python manage.py migrate && \
    python manage.py makemigrations drive --noinput && \
    python manage.py migrate drive && \

    python manage.py jobserver
fi