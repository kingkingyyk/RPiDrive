# RPi Drive
![Coverage Result](https://gitlab.com/kingkingyyk/RPiDrive/badges/ng_develop/coverage.svg)
![Pipeline Result](https://gitlab.com/kingkingyyk/RPiDrive/badges/ng_develop/pipeline.svg)

A cloud drive based on [Django](https://www.djangoproject.com/) & [Angular Material](https://material.angular.io/).

### Development Guide
Please install [Python 3.8+](https://www.python.org/downloads/) & [Node.js 14](https://nodejs.org/en/download/releases/)

```
git clone https://gitlab.com/kingkingyyk/RPiDrive.git
cd RPiDrive/backend
pip install -r requirements.txt
pip install -r requirements-test.txt
#Usual django stuffs
python manage.py runserver
```