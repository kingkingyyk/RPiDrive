### Getting Started
#### Prerequisite
* Linux (I use Virtualbox + [Ubuntu 20](https://ubuntu.com/download/desktop))
* [Python 3.8+](https://www.python.org/downloads/)
* [Node.js 14](https://nodejs.org/en/download/releases/)
* [VSCode](https://code.visualstudio.com/)
* [Docker](https://hub.docker.com/)

#### Libraries Installation
```bash
git clone https://gitlab.com/kingkingyyk/RPiDrive.git
cd RPiDrive/backend
pip install -r requirements.txt
pip install -r requirements-test.txt
cd ../RPiDrive/frontend
npm install --global npm@6
npm install @angular/cli -g
npm install
```

#### Initialization
```bash
# In backend folder
docker-compose -f docker-compose-dev.yaml up -d
python3 manage.py makemigrations
python3 manage.py migrate
cp config.yaml.sample config.yaml
# Fill in the config.yaml values, refer to deployment guide if not sure about the values.
```

#### Start Dev Server
```bash
# In backend folder
python3 manage.py runserver
# In frontend folder
ng serve
# Site is available at http://localhost:4200/drive/login
```