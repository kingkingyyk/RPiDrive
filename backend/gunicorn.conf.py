from multiprocessing import cpu_count
from psycogreen.gevent import patch_psycopg

def post_fork(server, worker):
    patch_psycopg()

bind = '0.0.0.0:8000'
workers = 2
worker_class = 'gevent'
worker_connections = 40
timeout = 600
