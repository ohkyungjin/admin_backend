from django.apps import AppConfig
from django.conf import settings


class ReservationsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "reservations"
    
    def ready(self):
        if settings.DEBUG:
            # 개발 서버에서 두 번 실행되는 것을 방지
            import os
            if os.environ.get('RUN_MAIN', None) != 'true':
                return
                
        # APScheduler 설정
        from django_apscheduler.jobstores import DjangoJobStore
        from apscheduler.schedulers.background import BackgroundScheduler
        from django.utils import timezone
        from datetime import datetime
        
        scheduler = BackgroundScheduler(timezone=settings.TIME_ZONE)
        scheduler.add_jobstore(DjangoJobStore(), "default")
        
        # 예약 상태 체크 작업 등록
        from .cron import check_reservation_status
        scheduler.add_job(
            check_reservation_status,
            'interval',
            minutes=1,
            name='check_reservation_status',
            jobstore='default',
            id='check_reservation_status',
            replace_existing=True,
            next_run_time=datetime.now(tz=timezone.get_current_timezone())
        )
        
        scheduler.start()
    