import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'DataHunter.settings')
app = Celery(
    'DataHunter',
    backend=f"redis://{os.getenv('REDIS_HOST', 'localhost')}:6379/0",
    broker=f"redis://{os.getenv('REDIS_HOST', 'localhost')}:6379/1"
)
app.conf.imports = (
    "celery_app.crawlers.symptoms",
    "celery_app.crawlers.gov_datas",
)
app.conf.timezone = 'Asia/Taipei'
app.conf.enable_utc = True
app.conf.beat_schedule = {
    'symptoms-crawler-weekly': {
        'task': 'celery_app.crawlers.symptoms.period_send_symptom_crawler_task',
        'schedule': crontab(hour=1, minute=0, day_of_week=0),  # 每週日凌晨1點執行
        'options': {'queue': 'dynamic_crawler_queue'},
    },
    'gov-data-crawler-daily': {
        'task': 'celery_app.crawlers.gov_datas.period_crawl_government_datasets',
        'schedule': crontab(hour=1, minute=0),  # 每天凌晨1點執行
        'options': {'queue': 'static_crawler_queue'},
    },
}

app.conf.task_routes = {
    'celery_app.crawlers.symptoms.*': {'queue': 'dynamic_crawler_queue'},
    'celery_app.crawlers.gov_datas.*': {'queue': 'static_crawler_queue'},
}

app.conf.task_default_queue = 'default'


