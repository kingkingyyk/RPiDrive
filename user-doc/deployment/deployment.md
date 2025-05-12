# Deployment

## Basic Setup

- Currently supported OS are `Raspbian` & `Ubuntu`. You may try other Linux distro but they are not guaranteed to work.
- The available releases are [here](https://gitlab.com/kingkingyyk/RPiDrive/container_registry/1473316)
- Install [Docker](https://docs.docker.com/engine/install/) & [Docker-Compose](https://docs.docker.com/compose/install/).
- Create a new folder with the following empty folders :

```bash
postgres
redis
temp
logs
config
```

- Generate a key with [Djecrety](https://djecrety.ir/).
- Create a `config.yaml` file in the `config` folder with the content below (Fill in your values when needed) :

```yaml
web:
  debug: false
  secret-key: "<your secret key from Djecrety>"
  time-zone: "<your timezone in tz database, i.e. Asia/Kuala_Lumpur>"
  temp-dir: "/drive/temp-dir"
indexer:
  period: 180
database:
  host: "postgres"
  port: 5432
  name: "<put a database name>"
  user: "<put a database user>"
  password: "<put a database password>"
redis:
  host: "redis"
  port: 6379
  db: 0
security:
  block-spam: true
  block-trigger: 5
  block-duration: 600
  domain:
    - https://www.myurl.com
reverse-proxy:
  ip-header: null
```

- Create a `docker-compose.yml` file in the new folder (Fill in your values when needed) :

```yaml
version: "3"

services:
  redis:
    image: "redis:7.2.1-bookworm"
    container_name: "redis"
    expose:
      - "6379"
    volumes:
      - ./redis:/data
    restart: always
  db:
    image: "postgres:16.0"
    container_name: "postgres"
    expose:
      - "5432"
    environment:
      POSTGRES_USER: "<database user in config.yaml>"
      POSTGRES_PASSWORD: "<database password in config.yaml>"
      POSTGRES_DB: "<database name in config.yaml>"
    volumes:
      - ./postgres:/var/lib/postgresql/data
    restart: always
  web:
    image: "registry.gitlab.com/kingkingyyk/rpidrive:<version>"
    container_name: rpidrive
    environment:
      - TZ=<timezone in config.yaml>
      - MODE=web
    ports:
      - "8000:8000"
    volumes:
      - ./temp:/drive/temp-dir
      - ./config:/app/.config
      - ./migrations:/app/drive/migrations
      - ./logs:/app/logs
      - <Path in host containing data>:<Mounted path in container>
      # Feel free to mount if you have more paths!
    depends_on:
      - redis
      - db
    restart: always
  jobserver:
    image: "registry.gitlab.com/kingkingyyk/rpidrive:<version>"
    container_name: rpidrive_jobserver
    environment:
      - TZ=<timezone in config.yaml>
      - MODE=jobserver
    volumes:
      - ./temp:/drive/temp-dir
      - ./config:/app/.config
      - ./migrations:/app/drive/migrations
      - ./logs:/app/logs
      - <Path in host containing data>:<Mounted path in container>
      # Feel free to mount if you have more paths!
    depends_on:
      - redis
      - db
    restart: always
```

- Start the everything with `docker-compose up -d`.
- Run `docker compose logs rpidrive_jobserver` to get the auto generated username & password.
- Visit `http://<host>:8000/drive/login` and login with the credential.
  - Make sure the storage provider path is the path mounted into container instead of the path on the host.
  - You can change the web server port by changing the port mapping in `rpidrive` container in `docker-compose.yml`

## Reverse Proxy Setup

It is a good idea to run this service behind `nginx`. Here are some extra configurations needed.

```
# In nginx config server block
client_max_body_size 100G; # Or increase to any value you want.
proxy_request_buffering off;

location /drive/ {
    proxy_pass http://localhost:<Your RPi Drive Web Port>/drive/;

    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header HOST $http_host;

    if ($invalid_referer) {
        return   403;
    }
}
```

```
# In config.yaml
reverse-proxy:
    ip-header: 'HTTP_X_FORWARDED_FOR'
```

## Public Instance

- Do reverse proxy setup
- Redirect http requests to https (You can do this in `nginx`)
- Implement https
