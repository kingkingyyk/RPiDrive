if [ "$MODE" == "standalone" ]; then
    python manage.py makemigrations --noinput && \
    python manage.py migrate && \
    python manage.py makemigrations drive --noinput && \
    python manage.py migrate drive && \

    python manage.py jobserver &
    gunicorn rpidrive.wsgi
fi

if [ "$MODE" == "core" ]; then
    python manage.py makemigrations --noinput && \
    python manage.py migrate && \
    python manage.py makemigrations drive --noinput && \
    python manage.py migrate drive && \

    python manage.py jobserver
fi

if [ "$MODE" == "web" ]; then
    gunicorn rpidrive.wsgi
fi