# RPi Drive

A cloud drive based on [Django](https://www.djangoproject.com/) & [Materialize CSS](https://materializecss.com/).

#### Development Guide
- Install Docker & Docker-Compose
```
git clone https://www.github.com/kingkingyyk/RPiDrive.git
cd RPiDrive/docker
docker compose up -d
```
- Install Python 3.7+
```
cd ../backend
pip install -r requirements.txt
python manage.py makemigrations
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
- Install Node
```
cd ../frontend
ng serve
```
- Go to `http://localhost:4200/drive/folder/1`
- ..... This is a development branch and more information will be updated.


#### Features to be added
- Refer to [issues](https://github.com/kingkingyyk/RPiDrive/issues).