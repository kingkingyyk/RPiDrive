python manage.py makemigrations --noinput && \
python manage.py migrate && \
python manage.py makemigrations drive --noinput && \
python manage.py migrate drive && \

python manage.py jobserver &
gunicorn rpidrive.wsgi