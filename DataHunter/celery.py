import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'DataHunter.settings')
app = Celery(
    'DataHunter',
    backend=f"redis://{os.getenv('REDIS_HOST', 'localhost')}:6379/0",
    broker=f"redis://{os.getenv('REDIS_HOST', 'localhost')}:6379/1"
)

app.conf.imports = (
    "celery_app.crawlers",
)


