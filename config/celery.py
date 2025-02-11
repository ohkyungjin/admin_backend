from celery import Celery
from celery.schedules import crontab
import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('cielopet')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

# Celery Beat 스케줄 설정
app.conf.beat_schedule = {
    'check-reservations-every-5-minutes': {
        'task': 'reservations.tasks.check_and_complete_reservations',
        'schedule': crontab(minute='*/1'),  # 5분마다 실행
    },
}

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}') 