web: gunicorn --config gunicorn_config.py wsgi:application
worker: celery -A edp_mvp.app.celery worker --loglevel=info --concurrency=1
beat: celery -A edp_mvp.app.celery beat --loglevel=info
