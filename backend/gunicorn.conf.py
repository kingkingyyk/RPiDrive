from gevent import monkey

from multiprocessing import cpu_count


def post_fork(server, worker):
    monkey.patch_all()


bind = "0.0.0.0:8000"
workers = 2
worker_class = "gevent"
worker_connections = 40
timeout = 600
