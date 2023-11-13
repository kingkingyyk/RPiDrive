# Updating to New Version

Bring up the containers then run the following commands (Container name are subjected to your deployment).

## Cleanup database

```
docker exec -it <database container name> psql -U <database user> <database name>
delete from django_migrations;
exit
```

## Update database

```
docker exec -it <rpi drive container name> python manage.py migrate rpidrive --run-syncdb
docker exec -it <rpi drive container name> python manage.py migrate --fake contenttypes
docker exec -it <rpi drive container name> python manage.py migrate --fake auth
docker exec -it <rpi drive container name> python manage.py migrate --fake admin
docker exec -it <rpi drive container name> python manage.py migrate --fake rpidrive
docker exec -it <rpi drive container name> python manage.py migrate --fake sessions
docker exec -it <rpi drive container name> python manage.py makemigrations rpidrive
docker exec -it <rpi drive container name> python manage.py migrate rpidrive
```
