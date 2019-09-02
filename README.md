# RPi Drive

A cloud drive based on [Django](https://www.djangoproject.com/) & [Materialize CSS](https://materializecss.com/).

#### Usage
```
git clone https://www.github.com/kingkingyyk/RPiDrive.git
cd RPiDrive
pip install -r requirements.txt
python manage.py makemigrations drive
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```
- Go to `http://localhost:8000/admin/`
- Add a drive object
- Add a path to storage object, set it as primary, link it to the drive object you created just now.
- Go to `http://localhost:8000/drive/`
- Perform login on superuser

#### For Production
- Please set DEBUG to False in `rpidrive/settings.py`
- Please change the SECRET_KEY in `rpidrive/settings.py`
- Disable admin project
- Run nginx as reverse proxy

#### Features to be added
- Hot standby
- Permission
- Storage management
- Download management