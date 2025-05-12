#!/bin/bash
set -eu -o pipefail

# Create admin UI data
python manage.py collectstatic --no-input

if [ "$MODE" == "web" ]; then
    gunicorn backend.wsgi
fi

if [ "$MODE" == "jobserver" ]; then
    python manage.py makemigrations --noinput && \
    python manage.py migrate && \
    python manage.py makemigrations rpidrive --noinput && \
    python manage.py migrate rpidrive && \

    python manage.py jobserver
fi
