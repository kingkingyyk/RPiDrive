# RPi Drive

A cloud drive based on [Django](https://www.djangoproject.com/) & [Materialize CSS](https://materializecss.com/).

#### Development Guide
```
git clone https://www.github.com/kingkingyyk/RPiDrive.git
cd RPiDrive
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

#### Production Guide
- Run the steps in Development Guide
- Deploy PostgreSQL
  ```
    sudo apt install postgresql libpq-dev postgresql-client postgresql-client-common -y
    sudo su postgres
    createuser someuser -P --interactive
    psql
    create database RPiDrive;
    \q
    exit
  ```
- In `rpidrive/settings.py`
  - Set DEBUG to False
  - Change the SECRET_KEY (50 characters)
  - Configure database (remember to update the username and password!)
    ```
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql_psycopg2',
            'NAME': 'RPiDrive',
            'USER': 'someuser',
            'PASSWORD': 'somepassword',
            'HOST': 'localhost',
            'PORT': '',
        }
    }
    ```
  - Create a temp folder in the drive of your primary storage folder (__not in the primary storage folder!!!__) and set FILE_UPLOAD_TEMP_DIR to it.
- Disable admin project by commenting out the /admin line in `drive/urls.py`
- Create `RPiDrive.service` in `/etc/systemd/system` with the following content:
   ```
    [Unit]
    Description=RPi Drive
    After=network.target
    
    [Service]
    ExecStart=gunicorn -w 9 -b 0.0.0.0:<port> rpidrive.wsgi --timeout 3000 --preload
    WorkingDirectory=<RPiDrive git clone location>
    
    [Install]
    WantedBy=multi-user.target
    ```
- Deploy Web Server
    ```
    sudo pip3 install gunicorn
    sudo apt-get install nginx -y
    ```
- Configure `\etc\nginx\sites-enabled\drive.conf`
    ```
    server {
        server_name <my domain name / ddns name>
        error_page 404      /s/404.html;
        error_page 403 =404 /s/404.html;
        location /s/404.html { internal; }
        client_max_body_size 5G;
        
        location /drive/ {
            proxy_pass  http://localhost:<gunicorn port>/drive/;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_read_timeout 3000s;
            proxy_request_buffering off;
    
            location /drive/static/ {
                alias <RPiDrive git clone location>/static/;
                try_files $uri static/$uri;
            }
        }
    }
    ```
- Enable HTTPS
    ```
    sudo apt-get install certbot python-certbot-nginx -y
    sudo certbot --nginx -d <my domain name / ddns name>
    ```
- Enable autostart
    ```
    sudo systemctl systemctl-reload
    sudo systemctl enable RPiDrive
    sudo systemctl start RPiDrive
    sudo systemctl enable nginx
    sudo systemctl start nginx
    ```

#### Common Issues
- Nginx shows 502 error
  - Set DEBUG_MODE to True in `drive/settings.py`
  - Run `sudo systemctl restart RPiDrive`
  - Refresh your browser
  - Run `sudo systemctl status RPiDrive` to check for the error
- Certbot error
  - Please verify your domain name / ddns can be resolved by others
- Update to new version
  - This software is not finalized yet, and subject to cause your production data to void. But typically you can run the following command to update :
    ```
    sudo systemctl stop RPiDrive
    cd <RPiDrive git clone location>
    git pull //If you run into settings.py conflict, please backup the settings.py to somewhere else, then restore it after git pull)
    python manage.py makemigrations
    python manage.py makemigrations drive
    python manage.py migrate
    sudo systemctl start RPiDrive
    ```
  - If the update step cause your RPiDrive to fail:
    - Run the commands
        ```
        cd <RPiDrive git clone location>
        sudo rm -R drive/migrations
        ```
    - Clear the database
    - Run the commands
        ```
        cd <RPiDrive git clone location>
        python manage.py makemigrations
        python manage.py makemigrations drive
        python manage.py migrate
        python manage.py createsuperuser
        python manage.py runserver
        ```
    - Then you can follow the remaining steps in Development Guide again.

#### Features to be added
- Refer to [issues](https://github.com/kingkingyyk/RPiDrive/issues).