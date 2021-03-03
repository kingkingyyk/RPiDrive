python manage.py makemigrations --noinput && \
python manage.py migrate && \
python manage.py makemigrations drive --noinput && \
python manage.py migrate drive && \

python manage.py jobserver &
gunicorn --workers=5 --threads=4 --bind=0.0.0.0:8000 --timeout=86400 rpidrive.wsgi