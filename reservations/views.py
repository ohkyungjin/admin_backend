from django.shortcuts import render
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from django.db import transaction
import logging
from datetime import datetime, timedelta
import pytz
from .models import (
    Customer, Pet, MemorialRoom, Reservation,
    ReservationHistory
)
from .serializers import (
    CustomerSerializer, PetSerializer, MemorialRoomSerializer,
    ReservationListSerializer, ReservationDetailSerializer,
    ReservationCreateSerializer, ReservationHistorySerializer,
    ReservationUpdateSerializer
)

logger = logging.getLogger(__name__)


class CustomerViewSet(viewsets.ModelViewSet):
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'phone', 'email']


class PetViewSet(viewsets.ModelViewSet):
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


class ReservationViewSet(viewsets.ModelViewSet):
    queryset = Reservation.objects.all()
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['status', 'is_emergency', 'assigned_staff']
    search_fields = [
        'customer__name', 'customer__phone',
        'pet__name', 'referral_hospital'
    ]

    def get_serializer_class(self):
        if self.action == 'list':
            return ReservationListSerializer
        elif self.action == 'create':
            return ReservationCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return ReservationUpdateSerializer
        return ReservationDetailSerializer

    def get_queryset(self):
        queryset = super().get_queryset().select_related(
            'customer', 'pet', 'package', 'memorial_room',
            'assigned_staff', 'created_by'
        ).prefetch_related('histories')

        # 날짜 필터링
        date = self.request.query_params.get('date')
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        memorial_room_id = self.request.query_params.get('memorial_room_id')
        client_timezone = self.request.query_params.get('timezone', 'Asia/Seoul')
        
        try:
            if date:
                try:
                    # RFC 2822 형식의 날짜 파싱 시도
                    date_obj = datetime.strptime(date, '%a, %d %b %Y %H:%M:%S %Z')
                except ValueError:
                    try:
                        # ISO 형식의 날짜 파싱 시도
                        date_obj = datetime.fromisoformat(date.replace('Z', '+00:00'))
                    except ValueError:
                        # 기본 YYYY-MM-DD 형식 시도
                        date_obj = datetime.strptime(date, '%Y-%m-%d')
                
                date_aware = timezone.make_aware(date_obj, pytz.timezone(client_timezone))
                queryset = queryset.filter(
                    scheduled_at__date=date_aware.date()
                )
            
            if start_date:
                start_dt = timezone.datetime.strptime(start_date, '%Y-%m-%d')
                start_dt = timezone.make_aware(start_dt, pytz.timezone(client_timezone))
                queryset = queryset.filter(scheduled_at__gte=start_dt)
            
            if end_date:
                end_dt = timezone.datetime.strptime(end_date, '%Y-%m-%d')
                end_dt = timezone.make_aware(end_dt, pytz.timezone(client_timezone))
                end_dt = end_dt.replace(hour=23, minute=59, second=59)
                queryset = queryset.filter(scheduled_at__lte=end_dt)

            if memorial_room_id:
                queryset = queryset.filter(memorial_room_id=memorial_room_id)

        except (ValueError, pytz.exceptions.UnknownTimeZoneError) as e:
            logger.error(f"Invalid date format or timezone: date={date}, start_date={start_date}, end_date={end_date}, timezone={client_timezone}")
            logger.error(f"Error details: {str(e)}")

        return queryset

    @action(detail=False, methods=['post'], url_path='bulk-status-update')
    def bulk_status_update(self, request):
        """여러 예약의 상태를 일괄 변경합니다."""
        reservation_ids = request.data.get('reservation_ids', [])
        new_status = request.data.get('status')
        notes = request.data.get('notes', '')

        logger.info(f"Bulk status update requested: ids={reservation_ids}, new_status={new_status}")

        if not reservation_ids or not new_status:
            return Response(
                {"error": "예약 ID 목록과 변경할 상태는 필수입니다."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if new_status not in dict(Reservation.STATUS_CHOICES):
            return Response(
                {"error": "올바르지 않은 상태입니다."},
                status=status.HTTP_400_BAD_REQUEST
            )

        success_count = 0
        failed_updates = []

        with transaction.atomic():
            reservations = Reservation.objects.select_for_update().filter(id__in=reservation_ids)
            
            for reservation in reservations:
                try:
                    logger.info(f"Processing reservation {reservation.id}: current_status={reservation.status}, new_status={new_status}")
                    
                    if not self._is_valid_status_transition(reservation.status, new_status):
                        error_msg = f"잘못된 상태 변경입니다. (현재: {reservation.status} → 요청: {new_status})"
                        logger.warning(f"Invalid status transition for reservation {reservation.id}: {error_msg}")
                        failed_updates.append({
                            "id": reservation.id,
                            "error": error_msg,
                            "current_status": reservation.status,
                            "requested_status": new_status
                        })
                        continue

                    old_status = reservation.status
                    reservation.status = new_status
                    reservation.save()

                    ReservationHistory.objects.create(
                        reservation=reservation,
                        from_status=old_status,
                        to_status=new_status,
                        changed_by=request.user,
                        notes=notes
                    )

                    success_count += 1
                    logger.info(f"Successfully updated reservation {reservation.id}: {old_status} → {new_status}")

                except Exception as e:
                    logger.error(f"Failed to update reservation {reservation.id}: {str(e)}")
                    failed_updates.append({
                        "id": reservation.id,
                        "error": str(e)
                    })

        response_data = {
            "success": True,
            "updated_count": success_count,
            "failed_updates": failed_updates
        }

        logger.info(f"Bulk update completed: success={success_count}, failures={len(failed_updates)}")
        return Response(response_data, status=status.HTTP_200_OK)

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
                reservation.status = new_status
                reservation.save()

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

    def _is_valid_status_transition(self, current_status, new_status):
        """상태 변경이 유효한지 검사합니다."""
        valid_transitions = {
            'pending': ['confirmed', 'cancelled'],
            'confirmed': ['in_progress', 'cancelled'],
            'in_progress': ['completed'],
            'completed': [],
            'cancelled': []
        }
        return new_status in valid_transitions.get(current_status, [])

    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @action(detail=False, methods=['GET'])
    def available_times(self, request):
        """특정 날짜의 예약 가능한 시간대를 조회합니다."""
        date_str = request.query_params.get('date')
        memorial_room_id = request.query_params.get('memorial_room_id')
        
        if not date_str:
            return Response(
                {"error": "날짜를 지정해주세요."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            
            # 과거 날짜 체크
            if target_date < timezone.now().date():
                return Response(
                    {"error": "과거 날짜는 조회할 수 없습니다."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # 기본 운영 시간 설정 (09:00 ~ 22:00)
            operating_hours = {
                'start': '09:00:00',
                'end': '22:00:00'
            }

            # 해당 날짜의 예약된 시간대 조회
            reservations = Reservation.objects.filter(
                scheduled_at__date=target_date,
                status__in=['pending', 'confirmed', 'in_progress']
            )

            if memorial_room_id:
                reservations = reservations.filter(memorial_room_id=memorial_room_id)

            # 예약된 시간대를 제외한 가용 시간대 계산
            reserved_times = [
                {
                    'start': r.scheduled_at.time(),
                    'end': (r.scheduled_at + timedelta(hours=2)).time()
                }
                for r in reservations
            ]

            # 가용 시간대 계산 로직 구현
            available_times = []
            current_time = datetime.strptime(operating_hours['start'], '%H:%M:%S').time()
            end_time = datetime.strptime(operating_hours['end'], '%H:%M:%S').time()

            while current_time < end_time:
                slot_end = (datetime.combine(target_date, current_time) + timedelta(hours=2)).time()
                is_available = True

                for reserved in reserved_times:
                    if (current_time >= reserved['start'] and current_time < reserved['end']) or \
                       (slot_end > reserved['start'] and slot_end <= reserved['end']):
                        is_available = False
                        break

                if is_available:
                    available_times.append({
                        'start_time': current_time.strftime('%H:%M:%S'),
                        'end_time': slot_end.strftime('%H:%M:%S')
                    })

                current_time = (datetime.combine(target_date, current_time) + timedelta(hours=1)).time()

            return Response({
                'date': date_str,
                'memorial_room_id': memorial_room_id,
                'available_times': available_times
            })

        except ValueError:
            return Response(
                {"error": "날짜 형식이 올바르지 않습니다. (YYYY-MM-DD)"},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=False, methods=['POST'])
    def check_availability(self, request):
        """예약 시간대 중복 여부를 체크합니다."""
        memorial_room_id = request.data.get('memorial_room_id')
        scheduled_at = request.data.get('scheduled_at')
        duration_hours = request.data.get('duration_hours', 2)

        if not all([memorial_room_id, scheduled_at]):
            return Response(
                {"error": "추모실 ID와 예약 시간은 필수입니다."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            scheduled_dt = timezone.datetime.fromisoformat(scheduled_at)
            end_dt = scheduled_dt + timedelta(hours=duration_hours)

            # 과거 시간 체크
            if scheduled_dt < timezone.now():
                return Response(
                    {"error": "과거 시간으로 예약할 수 없습니다."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # 중복 예약 체크
            conflicting_reservation = Reservation.objects.filter(
                memorial_room_id=memorial_room_id,
                scheduled_at__lt=end_dt,
                status__in=['pending', 'confirmed', 'in_progress']
            ).filter(
                scheduled_at__gt=scheduled_dt - timedelta(hours=duration_hours)
            ).first()

            if conflicting_reservation:
                return Response({
                    "is_available": False,
                    "conflicting_reservation": {
                        "id": conflicting_reservation.id,
                        "scheduled_at": conflicting_reservation.scheduled_at,
                        "duration_hours": duration_hours
                    }
                })

            return Response({
                "is_available": True,
                "conflicting_reservation": None
            })

        except ValueError:
            return Response(
                {"error": "날짜/시간 형식이 올바르지 않습니다."},
                status=status.HTTP_400_BAD_REQUEST
            )
