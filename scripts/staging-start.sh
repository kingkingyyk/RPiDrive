export SECRET_KEY="fncxsng(81-$ruzd$h-w3v8f-qj)2e)u*$w+f&!c!)7mx62^oq"
export DB_USER=postgres
export DB_PASSWORD=postgres
export DB_HOST=localhost
export DB_PORT=5432
export ARIA2_HOST=localhost
export ARIA2_PORT=6800
export ARIA2_SECRET=rpidrive
export ARIA2_DISK_CACHE=256M
export ALLOWED_HOSTS=*
export ADMIN_USER=rpidrive
export ADMIN_PASSWORD=rpidrivepass
export STORAGE_DIR=/home/lel/shared
cd ../backend
python3.7 manage.py runserver 0.0.0.0:8000 --settings=RPiDrive_ng.settings.prod