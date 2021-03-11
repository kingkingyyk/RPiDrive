from multiprocessing import cpu_count
from psycogreen.gevent import patch_psycopg

def post_fork(server, worker):
    patch_psycopg()

bind = '0.0.0.0:8000'
workers = cpu_count()
threads = 4
worker_class = 'gevent'
timeout = 86400
