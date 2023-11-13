### Getting Started

#### Prerequisite

- Linux (I use Virtualbox + [Ubuntu 22](https://ubuntu.com/download/desktop))
- [Python 3.12+](https://www.python.org/downloads/)
- [Node.js 20](https://nodejs.org/en/download/releases/)
- [VSCode](https://code.visualstudio.com/)
- [Docker](https://hub.docker.com/)

#### Libraries Installation

```bash
git clone https://gitlab.com/kingkingyyk/RPiDrive.git
cd RPiDrive/backend
python3 -m pip install -r requirements-dev.txt
cd ../RPiDrive/frontend
npm i react-scripts
npm i
```

#### Initialization

```bash
# In backend folder
docker compose -f docker-compose-dev.yaml up -d
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
npm start
# Site is available at http://localhost:3000/drive/login
```
