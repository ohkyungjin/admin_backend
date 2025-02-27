from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.request import Request
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from django.db import transaction
from django.db.models import QuerySet
import logging
from datetime import datetime, timedelta, time
import pytz
from typing import Any, List, Optional
from .models import (
    Customer, Pet, Reservation, ReservationHistory
)
from memorial_rooms.models import MemorialRoom
from .serializers import (
    CustomerSerializer, PetSerializer, MemorialRoomSerializer,
    ReservationListSerializer, ReservationDetailSerializer,
    ReservationCreateSerializer, ReservationHistorySerializer,
    ReservationUpdateSerializer
)

logger = logging.getLogger(__name__)


class CustomerViewSet(viewsets.ModelViewSet):
    """고객 정보 관리 ViewSet"""
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'phone', 'email']


class PetViewSet(viewsets.ModelViewSet):
    """반려동물 정보 관리 ViewSet"""
    queryset = Pet.objects.all()
    serializer_class = PetSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['customer', 'species']
    search_fields = ['name', 'breed']


class MemorialRoomViewSet(viewsets.ModelViewSet):
    queryset = MemorialRoom.objects.all()
    serializer_class = MemorialRoomSerializer

    @action(detail=False, methods=['GET'])
    def available(self, request):
        """특정 시간대에 예약 가능한 추모실 목록을 반환합니다."""
        date_str = request.query_params.get('date')
        if not date_str:
            return Response(
                {"error": "날짜를 지정해주세요."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            target_date = timezone.datetime.strptime(date_str, '%Y-%m-%d').date()
            # 해당 날짜에 예약된 추모실 ID 목록
            reserved_rooms = Reservation.objects.filter(
                scheduled_at__date=target_date,
                status__in=['pending', 'confirmed', 'in_progress']
            ).values_list('memorial_room_id', flat=True)

            # 예약 가능한 추모실만 필터링
            available_rooms = MemorialRoom.objects.exclude(
                id__in=reserved_rooms
            ).filter(is_active=True)

            serializer = self.get_serializer(available_rooms, many=True)
            return Response(serializer.data)
        except ValueError:
            return Response(
                {"error": "날짜 형식이 올바르지 않습니다. (YYYY-MM-DD)"},
                status=status.HTTP_400_BAD_REQUEST
            )


def validate_memorial_room(memorial_room_id: int) -> MemorialRoom:
    """추모실 ID 유효성 검사 및 객체 반환"""
    try:
        room = MemorialRoom.objects.get(id=memorial_room_id)
        if not room.is_active:
            raise ValueError("해당 추모실은 현재 사용할 수 없습니다.")
        return room
    except MemorialRoom.DoesNotExist:
        raise ValueError("존재하지 않는 추모실입니다.")

def handle_memorial_room_validation(memorial_room_id: int) -> tuple[bool, Optional[Response], Optional[MemorialRoom]]:
    """추모실 검증 처리 및 에러 응답 생성"""
    try:
        room = validate_memorial_room(memorial_room_id)
        return True, None, room
    except ValueError as e:
        error_response = Response(
            {
                "status": "error",
                "status_code": 400,
                "errors": {"memorial_room_id": [str(e)]}
            },
            status=status.HTTP_400_BAD_REQUEST
        )
        return False, error_response, None


class ReservationViewSet(viewsets.ModelViewSet):
    """예약 관리 ViewSet"""
    queryset = Reservation.objects.all()
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['status', 'is_emergency', 'assigned_staff']
    search_fields = [
        'customer__name', 'customer__phone',
        'pet__name', 'referral_hospital'
    ]

    def get_serializer_class(self):
        """요청 액션에 따른 시리얼라이저 클래스 반환"""
        if self.action == 'list':
            return ReservationListSerializer
        elif self.action == 'create':
            return ReservationCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return ReservationUpdateSerializer
        return ReservationDetailSerializer

    def get_queryset(self) -> QuerySet:
        """필터링이 적용된 쿼리셋 반환"""
        queryset = super().get_queryset().select_related(
            'customer', 'pet', 'package', 'memorial_room',
            'assigned_staff', 'created_by'
        ).prefetch_related('histories')

        try:
            return self._apply_date_filters(queryset)
        except (ValueError, pytz.exceptions.UnknownTimeZoneError) as e:
            logger.error(f"Date filtering error: {str(e)}")
            return queryset

    def _apply_date_filters(self, queryset: QuerySet) -> QuerySet:
        """날짜 기반 필터링 적용"""
        date = self.request.query_params.get('date')
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        memorial_room_id = self.request.query_params.get('memorial_room_id')
        client_timezone = self.request.query_params.get('timezone', 'Asia/Seoul')

        if date:
            date_obj = self._parse_date(date)
            date_aware = timezone.make_aware(date_obj, pytz.timezone(client_timezone))
            queryset = queryset.filter(scheduled_at__date=date_aware.date())

        if start_date:
            start_dt = timezone.make_aware(
                datetime.strptime(start_date, '%Y-%m-%d'),
                pytz.timezone(client_timezone)
            )
            queryset = queryset.filter(scheduled_at__gte=start_dt)

        if end_date:
            end_dt = timezone.make_aware(
                datetime.strptime(end_date, '%Y-%m-%d'),
                pytz.timezone(client_timezone)
            )
            end_dt = end_dt.replace(hour=23, minute=59, second=59)
            queryset = queryset.filter(scheduled_at__lte=end_dt)

        if memorial_room_id:
            queryset = queryset.filter(memorial_room_id=memorial_room_id)

        return queryset

    def _parse_date(self, date_str: str) -> datetime:
        """다양한 형식의 날짜 문자열을 파싱"""
        for fmt in ['%a, %d %b %Y %H:%M:%S %Z', '%Y-%m-%dT%H:%M:%S.%fZ', '%Y-%m-%d']:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        raise ValueError(f"Unsupported date format: {date_str}")

    @action(detail=False, methods=['post'], url_path='bulk-status-update')
    def bulk_status_update(self, request: Request) -> Response:
        """여러 예약의 상태를 일괄 변경"""
        reservation_ids = request.data.get('reservation_ids', [])
        new_status = request.data.get('status')
        notes = request.data.get('notes', '')

        logger.info(f"Bulk status update requested: ids={reservation_ids}, new_status={new_status}")

        if not self._validate_bulk_update_params(reservation_ids, new_status):
            return Response(
                {"error": "예약 ID 목록과 변경할 상태는 필수입니다."},
                status=status.HTTP_400_BAD_REQUEST
            )

        success_count, failed_updates = self._process_bulk_status_update(
            reservation_ids, new_status, notes, request.user
        )

        response_data = {
            "success": True,
            "updated_count": success_count,
            "failed_updates": failed_updates
        }

        logger.info(f"Bulk update completed: success={success_count}, failures={len(failed_updates)}")
        return Response(response_data, status=status.HTTP_200_OK)

    def _validate_bulk_update_params(self, reservation_ids: List[int], new_status: str) -> bool:
        """일괄 상태 변경 파라미터 검증"""
        if not reservation_ids or not new_status:
            return False
        return new_status in dict(Reservation.STATUS_CHOICES)

    def _process_bulk_status_update(
        self, 
        reservation_ids: List[int], 
        new_status: str, 
        notes: str,
        user: Any
    ) -> tuple[int, list]:
        """일괄 상태 변경 처리"""
        success_count = 0
        failed_updates = []

        with transaction.atomic():
            reservations = Reservation.objects.select_for_update().filter(id__in=reservation_ids)
            
            for reservation in reservations:
                try:
                    if not self._is_valid_status_transition(reservation.status, new_status):
                        error_msg = f"잘못된 상태 변경입니다. (현재: {reservation.status} → 요청: {new_status})"
                        self._add_failed_update(failed_updates, reservation, error_msg)
                        continue

                    self._update_reservation_status(reservation, new_status, notes, user)
                    success_count += 1

                except Exception as e:
                    logger.error(f"Failed to update reservation {reservation.id}: {str(e)}")
                    self._add_failed_update(failed_updates, reservation, str(e))

        return success_count, failed_updates

    def _add_failed_update(
        self, 
        failed_updates: list, 
        reservation: Reservation, 
        error: str
    ) -> None:
        """실패한 업데이트 정보 추가"""
        failed_updates.append({
            "id": reservation.id,
            "error": error,
            "current_status": reservation.status
        })

    def _update_reservation_status(
        self, 
        reservation: Reservation, 
        new_status: str, 
        notes: str,
        user: Any
    ) -> None:
        """예약 상태 업데이트 및 이력 생성"""
        old_status = reservation.status
        reservation.status = new_status
        reservation.save()

        ReservationHistory.objects.create(
            reservation=reservation,
            from_status=old_status,
            to_status=new_status,
            changed_by=user,
            notes=notes
        )

    def _is_valid_status_transition(self, current_status: str, new_status: str) -> bool:
        """상태 변경이 유효한지 검사"""
        valid_transitions = {
            Reservation.STATUS_PENDING: [Reservation.STATUS_CONFIRMED, Reservation.STATUS_CANCELLED],
            Reservation.STATUS_CONFIRMED: [Reservation.STATUS_IN_PROGRESS, Reservation.STATUS_CANCELLED],
            Reservation.STATUS_IN_PROGRESS: [Reservation.STATUS_COMPLETED],
            Reservation.STATUS_COMPLETED: [],
            Reservation.STATUS_CANCELLED: []
        }
        return new_status in valid_transitions.get(current_status, [])

    @action(detail=True, methods=['post'])
    def change_status(self, request, pk=None):
        """예약 상태를 변경합니다."""
        reservation = self.get_object()
        new_status = request.data.get('status')
        notes = request.data.get('notes', '')

        if not new_status:
            return Response(
                {"error": "새로운 상태를 지정해주세요."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if new_status not in dict(Reservation.STATUS_CHOICES):
            return Response(
                {"error": "올바르지 않은 상태입니다."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            with transaction.atomic():
                old_status = reservation.status
                
                # 예약 취소 시 처리
                if new_status == 'cancelled':
                    # 취소 시간 기록
                    reservation.cancelled_at = timezone.now()
                    
                    # 취소 사유 기록
                    cancel_reason = request.data.get('cancel_reason')
                    if cancel_reason:
                        reservation.cancel_reason = cancel_reason
                    
                    # 취소 비고 기록
                    cancel_notes = request.data.get('cancel_notes')
                    if cancel_notes:
                        reservation.cancel_notes = cancel_notes
                        
                    # 위약금 계산 및 기록
                    if reservation.can_cancel():
                        reservation.penalty_amount = reservation.calculate_penalty_amount()
                
                reservation.status = new_status
                reservation.save()

                # 상태 변경 이력 생성
                ReservationHistory.objects.create(
                    reservation=reservation,
                    from_status=old_status,
                    to_status=new_status,
                    changed_by=request.user,
                    notes=notes
                )

            serializer = ReservationDetailSerializer(reservation)
            return Response(serializer.data)
        except Exception as e:
            logger.error(f"Failed to change reservation status: {str(e)}")
            return Response(
                {"error": "상태 변경 중 오류가 발생했습니다."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['post'])
    def reschedule(self, request, pk=None):
        """예약 일정을 변경합니다."""
        reservation = self.get_object()
        new_datetime = request.data.get('scheduled_at')
        new_room_id = request.data.get('memorial_room_id')

        if not new_datetime:
            return Response(
                {"error": "새로운 예약 일시를 지정해주세요."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            with transaction.atomic():
                if new_room_id:
                    memorial_room = MemorialRoom.objects.get(id=new_room_id)
                    reservation.memorial_room = memorial_room

                reservation.scheduled_at = new_datetime
                reservation.save()

                ReservationHistory.objects.create(
                    reservation=reservation,
                    from_status=reservation.status,
                    to_status=reservation.status,
                    changed_by=request.user,
                    notes=f"일정 변경: {new_datetime}"
                )

            serializer = ReservationDetailSerializer(reservation)
            return Response(serializer.data)
        except MemorialRoom.DoesNotExist:
            return Response(
                {"error": "존재하지 않는 추모실입니다."},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Failed to reschedule reservation: {str(e)}")
            return Response(
                {"error": "일정 변경 중 오류가 발생했습니다."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def create(self, request, *args, **kwargs):
        """예약 생성"""
        memorial_room_id = request.data.get('memorial_room_id')
        if memorial_room_id:
            is_valid, error_response, room = handle_memorial_room_validation(memorial_room_id)
            if not is_valid:
                return error_response
            
        return super().create(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        """예약 수정"""
        memorial_room_id = request.data.get('memorial_room_id')
        if memorial_room_id:
            is_valid, error_response, room = handle_memorial_room_validation(memorial_room_id)
            if not is_valid:
                return error_response

        return super().update(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        """예약 부분 수정"""
        return self.update(request, *args, **kwargs)

    @action(detail=False, methods=['get'], url_path='available-times', url_name='available_times')
    def available_times(self, request):
        """예약 가능한 시간 목록을 반환합니다."""
        try:
            # 날짜 파라미터 검증
            date_str = request.query_params.get('date')
            if not date_str:
                return Response(
                    {"error": "날짜는 필수 파라미터입니다."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # 날짜 파싱
            try:
                target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            except ValueError:
                return Response(
                    {"error": "올바른 날짜 형식이 아닙니다. (YYYY-MM-DD)"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # KST 시간대 설정
            KST = pytz.timezone('Asia/Seoul')
            now = timezone.localtime(timezone.now(), KST)
            
            if target_date < now.date():
                return Response(
                    {"error": "과거 날짜는 선택할 수 없습니다."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # 기본 운영 시간 설정
            start_time = datetime.strptime('09:00', '%H:%M').time()
            end_time = datetime.strptime('22:30', '%H:%M').time()

            # 해당 날짜의 예약 목록 조회 (KST 기준)
            target_start = timezone.make_aware(datetime.combine(target_date, time.min), KST)
            target_end = timezone.make_aware(datetime.combine(target_date, time.max), KST)
            
            reservations = Reservation.objects.filter(
                scheduled_at__range=(target_start, target_end),
                status__in=['pending', 'confirmed', 'in_progress']
            ).order_by('scheduled_at')

            # 시간대별 예약 수 계산 (30분 단위)
            booking_counts = {}
            for reservation in reservations:
                # KST로 변환하여 시간 추출
                kst_time = timezone.localtime(reservation.scheduled_at, KST)
                time_str = kst_time.strftime('%H:%M')
                booking_counts[time_str] = booking_counts.get(time_str, 0) + 1

            # 시간 슬롯 생성 (30분 단위)
            available_times = []
            current_datetime = timezone.make_aware(datetime.combine(target_date, start_time), KST)
            end_datetime = timezone.make_aware(datetime.combine(target_date, end_time), KST)

            while current_datetime <= end_datetime:
                time_str = current_datetime.strftime('%H:%M')
                current_bookings = booking_counts.get(time_str, 0)
                
                # 예약 가능 여부 확인
                is_available = True
                
                # 현재 시간과 같거나 이전의 시간은 예약 불가
                if target_date == now.date():
                    current_time = now.strftime('%H:%M')
                    if time_str <= current_time:
                        is_available = False
                # 3개 이상 예약된 시간은 예약 불가
                elif current_bookings >= 3:
                    is_available = False

                available_times.append({
                    "time": time_str,
                    "current_bookings": current_bookings,
                    "is_available": is_available
                })

                current_datetime += timedelta(minutes=30)

            response_data = {
                "date": date_str,
                "operating_hours": {
                    "start": "09:00",
                    "end": "22:30"
                },
                "available_times": available_times
            }

            return Response({"data": response_data})

        except Exception as e:
            logger.error(f"Error in available_times: {str(e)}")
            return Response(
                {"error": "서버 오류가 발생했습니다."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['post'], url_path='check-availability', url_name='check_availability')
    def check_availability(self, request):
        """예약 시간 형식을 검증합니다."""
        scheduled_at = request.data.get('scheduled_at')
        duration_hours = request.data.get('duration_hours', 2)

        if not scheduled_at:
            return Response(
                {"error": "예약 시간은 필수입니다."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            scheduled_dt = timezone.datetime.fromisoformat(scheduled_at.replace('Z', '+00:00'))
            end_dt = scheduled_dt + timedelta(hours=duration_hours)

            return Response({
                "is_valid": True,
                "scheduled_at": scheduled_dt,
                "end_at": end_dt
            })

        except ValueError as e:
            logger.error(f"Invalid datetime format: {scheduled_at}, error: {str(e)}")
            return Response(
                {"error": "날짜/시간 형식이 올바르지 않습니다."},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['patch'], url_path='update-payment-info')
    def update_payment_info(self, request, pk=None):
        """예약의 결제 관련 정보(할증료, 할인)를 업데이트합니다."""
        reservation = self.get_object()
        
        try:
            with transaction.atomic():
                # 결제 정보 업데이트
                weight_surcharge = request.data.get('weight_surcharge')
                if weight_surcharge is not None:
                    reservation.weight_surcharge = weight_surcharge

                discount_type = request.data.get('discount_type')
                if discount_type is not None:
                    if discount_type not in dict(Reservation.DISCOUNT_TYPE_CHOICES):
                        return Response(
                            {"error": "올바르지 않은 할인 유형입니다."},
                            status=status.HTTP_400_BAD_REQUEST
                        )
                    reservation.discount_type = discount_type

                discount_value = request.data.get('discount_value')
                if discount_value is not None:
                    if discount_type == 'percent' and float(discount_value) > 100:
                        return Response(
                            {"error": "할인율은 100%를 초과할 수 없습니다."},
                            status=status.HTTP_400_BAD_REQUEST
                        )
                    reservation.discount_value = discount_value

                reservation.save()

                # 이력 생성
                ReservationHistory.objects.create(
                    reservation=reservation,
                    from_status=reservation.status,
                    to_status=reservation.status,
                    changed_by=request.user,
                    notes=f'결제 정보 업데이트 (할증료: {weight_surcharge}, 할인: {discount_type} {discount_value})'
                )

                serializer = ReservationDetailSerializer(reservation)
                return Response(serializer.data)

        except Exception as e:
            logger.error(f"Failed to update payment info for reservation {pk}: {str(e)}")
            return Response(
                {"error": "결제 정보 업데이트 중 오류가 발생했습니다."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
