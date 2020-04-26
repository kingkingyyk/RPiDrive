cd /mnt
export DJANGO_SETTINGS_MODULE=RPiDrive_ng.settings.prod
python manage.py makemigrations
python manage.py makemigrations drive
python manage.py makemigrations mediaplayer
python manage.py migrate
python manage.py migrate drive
python manage.py migrate mediaplayer
python manage.py initialize
python manage.py indexer
/usr/local/bin/gunicorn -w 9 -b 0.0.0.0:8888 RPiDrive_ng.wsgi --timeout 3000 --preload