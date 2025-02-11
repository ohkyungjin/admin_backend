from django.db import models
from django.utils import timezone

class DashboardWidget(models.Model):
    """대시보드 위젯 설정 모델"""
    WIDGET_TYPES = [
        ('reservation_stats', '예약 통계'),
        ('memorial_room_status', '추모실 현황'),
        ('recent_reservations', '최근 예약'),
        ('calendar', '일정 캘린더'),
        ('staff_workload', '직원 배정 현황'),
        ('alerts', '알림'),
    ]

    name = models.CharField('위젯 이름', max_length=100)
    widget_type = models.CharField('위젯 타입', max_length=50, choices=WIDGET_TYPES)
    is_active = models.BooleanField('활성화 여부', default=True)
    position = models.IntegerField('표시 순서', default=0)
    created_at = models.DateTimeField('생성일시', auto_now_add=True)
    updated_at = models.DateTimeField('수정일시', auto_now=True)

    class Meta:
        ordering = ['position']
        verbose_name = '대시보드 위젯'
        verbose_name_plural = '대시보드 위젯 목록'

    def __str__(self):
        return f"{self.get_widget_type_display()} - {self.name}"
