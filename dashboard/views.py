from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from django.db.models import Count, Q
from datetime import datetime, timedelta

from reservations.models import Reservation, MemorialRoom, ReservationHistory
from accounts.models import User
from .models import DashboardWidget
from .serializers import (
    DashboardWidgetSerializer,
    ReservationStatsSerializer,
    MemorialRoomStatusSerializer,
    StaffWorkloadSerializer,
    DashboardDataSerializer
)


class DashboardViewSet(viewsets.ViewSet):
    """대시보드 API ViewSet"""

    def _get_target_date(self, request):
        """요청에서 날짜 파라미터 처리"""
        today = timezone.now().date()
        date_param = request.query_params.get('date')
        
        if date_param:
            try:
                return datetime.strptime(date_param, '%Y-%m-%d').date()
            except ValueError:
                return today
        return today

    def list(self, request):
        """대시보드 전체 데이터 조회"""
        target_date = self._get_target_date(request)
        
        # 예약 통계 데이터
        reservation_stats = self._get_reservation_stats(target_date)
        
        # 추모실 현황 데이터
        memorial_room_status = self._get_memorial_room_status(target_date)
        
        # 해당 날짜의 예약 목록
        recent_reservations = Reservation.objects.filter(
            scheduled_at__date=target_date
        ).order_by('-created_at')
        
        # 직원 배정 현황
        staff_workload = self._get_staff_workload(target_date)

        # 전체 데이터 직렬화
        serializer = DashboardDataSerializer({
            'reservation_stats': reservation_stats,
            'memorial_room_status': memorial_room_status,
            'recent_reservations': recent_reservations,
            'staff_workload': staff_workload
        })
        
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def reservation_stats(self, request):
        """예약 통계 데이터 조회"""
        target_date = self._get_target_date(request)
        stats = self._get_reservation_stats(target_date)
        serializer = ReservationStatsSerializer(stats)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def memorial_room_status(self, request):
        """추모실 현황 데이터 조회"""
        target_date = self._get_target_date(request)
        status_data = self._get_memorial_room_status(target_date)
        serializer = MemorialRoomStatusSerializer(status_data, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def staff_workload(self, request):
        """직원 배정 현황 데이터 조회"""
        target_date = self._get_target_date(request)
        workload_data = self._get_staff_workload(target_date)
        serializer = StaffWorkloadSerializer(workload_data, many=True)
        return Response(serializer.data)

    def _get_reservation_stats(self, today):
        """예약 통계 데이터 생성"""
        # 오늘의 예약 통계
        today_stats = {
            'today_total': Reservation.objects.filter(scheduled_at__date=today).count(),
            'today_completed': Reservation.objects.filter(scheduled_at__date=today, status='completed').count(),
            'today_pending': Reservation.objects.filter(scheduled_at__date=today, status='pending').count(),
            'today_confirmed': Reservation.objects.filter(scheduled_at__date=today, status='confirmed').count(),
            'today_in_progress': Reservation.objects.filter(scheduled_at__date=today, status='in_progress').count(),
            'today_cancelled': Reservation.objects.filter(scheduled_at__date=today, status='cancelled').count(),
            'emergency_count': Reservation.objects.filter(
                scheduled_at__date=today,
                is_emergency=True,
                status__in=['pending', 'confirmed']
            ).count()
        }

        # 주간 통계
        week_start = today - timedelta(days=today.weekday())
        weekly_stats = {}
        for i in range(7):
            date = week_start + timedelta(days=i)
            weekly_stats[date.strftime('%Y-%m-%d')] = Reservation.objects.filter(
                scheduled_at__date=date
            ).count()

        # 월간 통계
        month_start = today.replace(day=1)
        monthly_stats = {}
        while month_start <= today:
            monthly_stats[month_start.strftime('%Y-%m-%d')] = Reservation.objects.filter(
                scheduled_at__date=month_start
            ).count()
            month_start += timedelta(days=1)

        return {**today_stats, 'weekly_stats': weekly_stats, 'monthly_stats': monthly_stats}

    def _get_memorial_room_status(self, today):
        """추모실 현황 데이터 생성"""
        now = timezone.now()
        status_data = []

        for room in MemorialRoom.objects.all():
            # 상태 자동 업데이트 처리
            # 1. 예약 시간이 된 예약을 진행중으로 변경
            confirmed_reservations = Reservation.objects.filter(
                memorial_room=room,
                scheduled_at__date=today,
                scheduled_at__lte=now,
                status='confirmed'
            )
            for reservation in confirmed_reservations:
                reservation.status = 'in_progress'
                reservation.save()
                # 예약 이력 생성
                ReservationHistory.objects.create(
                    reservation=reservation,
                    from_status='confirmed',
                    to_status='in_progress',
                    notes='예약 시간 도래로 자동 상태 변경'
                )

            # 2. 2시간이 지난 진행중 예약을 완료로 변경
            in_progress_reservations = Reservation.objects.filter(
                memorial_room=room,
                scheduled_at__date=today,
                scheduled_at__lte=now - timedelta(hours=2),
                status='in_progress'
            )
            for reservation in in_progress_reservations:
                reservation.status = 'completed'
                reservation.save()
                # 예약 이력 생성
                ReservationHistory.objects.create(
                    reservation=reservation,
                    from_status='in_progress',
                    to_status='completed',
                    notes='예약 시간 2시간 경과로 자동 완료 처리'
                )

            # 현재 진행중인 예약 확인
            current_reservation = Reservation.objects.filter(
                memorial_room=room,
                scheduled_at__date=today,
                status__in=['in_progress', 'confirmed']
            ).filter(
                Q(scheduled_at__lte=now + timedelta(hours=2))  # 현재 시간으로부터 2시간 이내에 시작하는 예약
            ).first()

            # 다음 예약 - 현재 시간 이후의 가장 빠른 예약
            next_reservation = Reservation.objects.filter(
                memorial_room=room,
                scheduled_at__date=today,
                status__in=['confirmed', 'pending']
            ).filter(
                Q(scheduled_at__gt=now if not current_reservation else current_reservation.scheduled_at + timedelta(hours=2))
            ).order_by('scheduled_at').first()

            # 오늘의 예약 수
            today_count = Reservation.objects.filter(
                memorial_room=room,
                scheduled_at__date=today,
                status__in=['pending', 'confirmed', 'in_progress']
            ).count()

            # 현재 예약과 다음 예약이 같은 경우 다음 예약은 None으로 설정
            if next_reservation and current_reservation and next_reservation.id == current_reservation.id:
                next_reservation = None

            status_data.append({
                'room_id': room.id,
                'room_name': room.name,
                'current_status': 'in_use' if current_reservation else 'available',
                'next_reservation': next_reservation,
                'today_reservation_count': today_count
            })

        return status_data

    def _get_staff_workload(self, today):
        """직원 배정 현황 데이터 생성"""
        workload_data = []

        # 해당 날짜의 예약이 있는 직원들 조회
        assigned_staff_ids = Reservation.objects.filter(
            scheduled_at__date=today
        ).values_list('assigned_staff', flat=True).distinct()

        # 예약이 있는 직원들의 정보와 배정된 예약 조회
        for staff_id in assigned_staff_ids:
            if staff_id is None:  # 배정되지 않은 예약은 건너뛰기
                continue
                
            staff = User.objects.get(id=staff_id)
            assigned_reservations = Reservation.objects.filter(
                assigned_staff=staff,
                scheduled_at__date=today
            ).order_by('scheduled_at')

            workload_data.append({
                'staff_id': staff.id,
                'staff_name': staff.name,
                'assigned_count': assigned_reservations.count(),
                'today_assignments': assigned_reservations
            })

        return workload_data
