from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from .models import Reservation, ReservationHistory
import logging

logger = logging.getLogger(__name__)

@shared_task
def check_and_complete_reservations():
    """진행중이거나 확정된 예약 중 2시간이 경과한 예약을 자동으로 완료 처리"""
    now = timezone.now()
    two_hours_ago = now - timedelta(hours=2)
    
    # 당일 예약 중 2시간이 지난 진행중 또는 확정 상태의 예약들 조회
    reservations = Reservation.objects.filter(
        status__in=[Reservation.STATUS_IN_PROGRESS, Reservation.STATUS_CONFIRMED],
        scheduled_at__lte=two_hours_ago,
        scheduled_at__date=now.date()  # 당일 예약만 필터링
    )
    
    completed_count = 0
    for reservation in reservations:
        try:
            # 로깅 추가
            logger.info(
                f"Auto completing reservation {reservation.id} "
                f"(status: {reservation.get_status_display()}, "
                f"scheduled at: {reservation.scheduled_at}, "
                f"current time: {now})"
            )
            
            previous_status = reservation.status
            reservation.status = Reservation.STATUS_COMPLETED
            reservation.save()
            
            # 예약 이력 생성
            ReservationHistory.objects.create(
                reservation=reservation,
                from_status=previous_status,
                to_status=Reservation.STATUS_COMPLETED,
                notes=f'{reservation.get_status_display()} 상태에서 2시간 경과로 자동 완료 처리'
            )
            completed_count += 1
            
        except Exception as e:
            logger.error(
                f"Failed to auto-complete reservation {reservation.id}: {str(e)}\n"
                f"Status: {reservation.get_status_display()}, "
                f"Scheduled at: {reservation.scheduled_at}, Current time: {now}"
            )
    
    if completed_count > 0:
        logger.info(f"Successfully completed {completed_count} reservations")
    
    return f"{completed_count} reservations auto-completed" 