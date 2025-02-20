from rest_framework import serializers
from django.db.models import Count, Sum
from django.utils import timezone
from datetime import datetime, timedelta

from reservations.models import Reservation
from reservations.serializers import ReservationListSerializer
from .models import DashboardWidget


class DashboardWidgetSerializer(serializers.ModelSerializer):
    """대시보드 위젯 시리얼라이저"""
    class Meta:
        model = DashboardWidget
        fields = '__all__'


class ReservationStatsSerializer(serializers.Serializer):
    """예약 통계 시리얼라이저"""
    today_total = serializers.IntegerField()
    today_completed = serializers.IntegerField()
    today_pending = serializers.IntegerField()
    today_confirmed = serializers.IntegerField()
    today_in_progress = serializers.IntegerField()
    today_cancelled = serializers.IntegerField()
    emergency_count = serializers.IntegerField()
    weekly_stats = serializers.DictField()
    monthly_stats = serializers.DictField()


class MemorialRoomStatusSerializer(serializers.Serializer):
    """추모실 현황 시리얼라이저"""
    room_id = serializers.IntegerField()
    room_name = serializers.CharField()
    current_status = serializers.CharField()
    next_reservation = serializers.SerializerMethodField()
    today_reservation_count = serializers.IntegerField()
    today_reservations = serializers.SerializerMethodField()

    def get_next_reservation(self, obj):
        if obj.get('next_reservation'):
            return obj['next_reservation']
        return None

    def get_today_reservations(self, obj):
        if obj.get('today_reservations'):
            return obj['today_reservations']
        return []


class StaffWorkloadSerializer(serializers.Serializer):
    """직원 배정 현황 시리얼라이저"""
    staff_id = serializers.IntegerField()
    staff_name = serializers.CharField()
    assigned_count = serializers.IntegerField()
    today_assignments = serializers.ListField(
        child=ReservationListSerializer()
    )


class DashboardDataSerializer(serializers.Serializer):
    """대시보드 전체 데이터 시리얼라이저"""
    reservation_stats = ReservationStatsSerializer()
    memorial_room_status = MemorialRoomStatusSerializer(many=True)
    recent_reservations = ReservationListSerializer(many=True)
    staff_workload = StaffWorkloadSerializer(many=True) 