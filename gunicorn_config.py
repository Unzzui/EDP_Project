# Configuración de Gunicorn para producción en Render
import os
import multiprocessing

# Server socket
bind = f"0.0.0.0:{os.environ.get('PORT', '5000')}"
backlog = 2048

# Worker processes - Mejor configuración para Render
workers = int(os.environ.get('WEB_CONCURRENCY', multiprocessing.cpu_count() * 2 + 1))
worker_class = 'sync'  # Usar workers síncronos para mayor estabilidad
worker_connections = 1000
threads = 2  # Añadir threads para manejar SocketIO con threading mode
timeout = 120  # Timeout más alto para requests largos
keepalive = 2

# Restart workers after serving this many requests, to help control memory usage
max_requests = 1000
max_requests_jitter = 100

# Logging
accesslog = "-"  # stdout
errorlog = "-"   # stderr
loglevel = "info"
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
user = None  # Render maneja el usuario automáticamente
group = None

# Configuración para proxy reverso (común en servicios cloud como Render)
forwarded_allow_ips = '*'
secure_scheme_headers = {
    'X-FORWARDED-PROTOCOL': 'ssl',
    'X-FORWARDED-PROTO': 'https',
    'X-FORWARDED-SSL': 'on'
}

def when_ready(server):
    server.log.info("🚀 Gunicorn server is ready. Spawning workers")
    server.log.info(f"🔧 Workers: {workers}, Timeout: {timeout}s")

def worker_int(worker):
    worker.log.info("⚠️  Worker received INT or QUIT signal")
    
def pre_fork(server, worker):
    server.log.info("👷 Worker spawned (pid: %s)", worker.pid)

def pre_exec(server):
    server.log.info("🔄 Forked child, re-executing.")

def post_fork(server, worker):
    server.log.info("✅ Worker spawned (pid: %s)", worker.pid)
