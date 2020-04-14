# RPi Drive

A cloud drive based on [Django](https://www.djangoproject.com/) & [Angular Material](https://material.angular.io/).

#### Development Guide
- Install Docker, Python3.7+, NodeJS
```
git clone https://www.github.com/kingkingyyk/RPiDrive.git
cd RPiDrive/frontend
npm install --save
cd ../backend
sudo apt install libpq-dev gcc python3.7-dev
python3.7 -m pip install -r requirements
cd ../docker
sudo docker-compose -f docker-compose-dev.yml up -d
```
- Change settings in `RPiDrive_ng/settings/dev.py
```
cd ../backend
python3.7 manage.py makemigrations
python3.7 manage.py migrate
python3.7 manage.py makemigrations drive
python3.7 manage.py migrate drive
python3.7 manage.py makemigrations mediaplayer
python3.7 manage.py migrate mediaplayer
python3.7 manage.py initialize
python3.7 manage.py indexer
python3.7 manage.py runserver 0.0.0.0:8000
cd ../frontend
ng serve
```
- Go to `http://localhost:4200`
- ..... This is a development branch and more information will be updated.


#### Features to be added
- Refer to [issues](https://github.com/kingkingyyk/RPiDrive/issues).