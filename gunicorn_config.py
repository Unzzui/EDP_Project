# Configuración de Gunicorn para producción
import os

# Server socket
bind = f"0.0.0.0:{os.environ.get('PORT', '5000')}"
backlog = 2048

# Worker processes
workers = int(os.environ.get('GUNICORN_WORKERS', '2'))
worker_class = 'eventlet'  # Para compatibilidad con SocketIO
worker_connections = 1000
timeout = 30
keepalive = 2

# Restart workers after serving this many requests, to help control memory usage
max_requests = 1000
max_requests_jitter = 100

# Logging
capture_output = True
enable_stdio_inheritance = True

# Security
limit_request_line = 4094
limit_request_fields = 100
limit_request_field_size = 8190

# Application preloading
preload_app = True

# Server mechanics
daemon = False
pidfile = None
tmp_upload_dir = None
user = None
group = None

def when_ready(server):
    server.log.info("Server is ready. Spawning workers")

def worker_int(worker):
    worker.log.info("worker received INT or QUIT signal")
    
def pre_fork(server, worker):
    server.log.info("Worker spawned (pid: %s)", worker.pid)

def pre_exec(server):
    server.log.info("Forked child, re-executing.")

def post_fork(server, worker):
    server.log.info("Worker spawned (pid: %s)", worker.pid)
