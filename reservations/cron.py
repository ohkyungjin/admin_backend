from django.utils import timezone
from datetime import timedelta
from .models import Reservation, ReservationHistory
from memorial_rooms.models import MemorialRoom
import logging

logger = logging.getLogger(__name__)

def check_reservation_status():
    """
    1분마다 실행되는 예약 상태 체크 함수
    1. 예약 시간으로부터 2시간이 지난 예약을 완료로 변경
    2. 예약 시간이 된 예약을 진행중으로 변경
    3. 추모실 상태 업데이트
    """
    now = timezone.now()
    logger.info(f"Starting reservation status check at {now}")
    
    try:
        # 1. 예약 시간으로부터 2시간이 지난 예약을 완료로 변경
        in_progress_reservations = Reservation.objects.filter(
            status='in_progress',
            scheduled_at__lte=now - timedelta(hours=2)  # 예약 시간으로부터 2시간이 지난 예약
        )
        
        completed_count = 0
        for reservation in in_progress_reservations:
            logger.info(
                f"Completing reservation {reservation.id} "
                f"(scheduled at: {reservation.scheduled_at}, current time: {now})"
            )
            
            # 상태 변경 및 이력 생성
            previous_status = reservation.status
            reservation.status = 'completed'
            reservation.save()
            
            ReservationHistory.objects.create(
                reservation=reservation,
                from_status=previous_status,
                to_status='completed',
                notes='예약 시간으로부터 2시간 경과로 자동 완료 처리',
                changed_by=None  # 시스템 자동 변경
            )
            completed_count += 1
        
        logger.info(f"Completed {completed_count} reservations")
        
        # 2. 예약 시간이 된 확정 상태의 예약을 진행중으로 변경
        confirmed_reservations = Reservation.objects.filter(
            status='confirmed',
            scheduled_at__lte=now  # 예약 시간이 현재 시간보다 이전인 모든 예약
        )
        
        started_count = 0
        for reservation in confirmed_reservations:
            logger.info(
                f"Starting reservation {reservation.id} "
                f"(scheduled at: {reservation.scheduled_at}, current time: {now})"
            )
            
            # 상태 변경 및 이력 생성
            previous_status = reservation.status
            reservation.status = 'in_progress'
            reservation.save()
            
            ReservationHistory.objects.create(
                reservation=reservation,
                from_status=previous_status,
                to_status='in_progress',
                notes='예약 시간 도래로 자동으로 진행중 상태로 변경',
                changed_by=None  # 시스템 자동 변경
            )
            started_count += 1
        
        logger.info(f"Started {started_count} reservations")
        
        # 3. 추모실 상태 업데이트
        updated_rooms = 0
        for room in MemorialRoom.objects.all():
            # 현재 진행중인 예약 확인
            current_reservation = Reservation.objects.filter(
                memorial_room=room,
                status__in=['confirmed', 'in_progress'],
                scheduled_at__lte=now + timedelta(hours=2)  # 2시간 이내 예정된 예약 포함
            ).order_by('scheduled_at').first()
            
            old_status = room.current_status
            if current_reservation:
                # 예약 시간이 아직 안된 경우
                if current_reservation.scheduled_at > now:
                    room.current_status = 'reserved'
                # 예약 시간이 된 경우
                else:
                    room.current_status = 'in_use'
            else:
                room.current_status = 'available'
            
            if old_status != room.current_status:
                logger.info(
                    f"Updating memorial room {room.id} status from {old_status} to {room.current_status}"
                )
                room.save()
                updated_rooms += 1
        
        logger.info(f"Updated {updated_rooms} memorial rooms")
        logger.info("Reservation status check completed successfully")
        
    except Exception as e:
        logger.error(f"Error during reservation status check: {str(e)}", exc_info=True)
        print(f'[ERROR] {timezone.now()} Error during reservation status check: {str(e)}') 