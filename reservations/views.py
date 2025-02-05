from django.shortcuts import render
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from django.db import transaction
import logging
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

        # 날짜 범위 필터링
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        
        if start_date:
            queryset = queryset.filter(scheduled_at__date__gte=start_date)
        if end_date:
            queryset = queryset.filter(scheduled_at__date__lte=end_date)

        return queryset

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        return response

    @transaction.atomic
    @action(detail=True, methods=['POST'])
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
            old_status = reservation.status
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

    @action(detail=True, methods=['POST'])
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
            if new_room_id:
                memorial_room = MemorialRoom.objects.get(id=new_room_id)
                reservation.memorial_room = memorial_room

            reservation.scheduled_at = new_datetime
            reservation.save()

            # 일정 변경 이력 생성
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

    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)
