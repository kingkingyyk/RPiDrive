# Updating to New Version (v2.x to v2.y)

Bring up the containers then run the following commands.

## Update database

```
docker exec -it rpidrive python manage.py makemigrations rpidrive
docker exec -it rpidrive python manage.py makemigrations
docker exec -it rpidrive python manage.py migrate rpidrive
```
