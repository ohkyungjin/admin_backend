from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from funeral.models import FuneralPackage, PremiumLine, AdditionalOption
from memorial_rooms.models import MemorialRoom
from django.utils import timezone
from decimal import Decimal
from typing import Optional, List, Dict
from datetime import datetime, timedelta


class Customer(models.Model):
    """고객 정보를 관리하는 모델"""
    name = models.CharField(_('고객명'), max_length=100)
    phone = models.CharField(_('전화번호'), max_length=20)
    email = models.EmailField(_('이메일'), blank=True)
    address = models.TextField(_('주소'), blank=True)
    created_at = models.DateTimeField(_('생성일'), auto_now_add=True)
    updated_at = models.DateTimeField(_('수정일'), auto_now=True)

    class Meta:
        verbose_name = _('고객')
        verbose_name_plural = _('고객 목록')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['phone']),
            models.Index(fields=['name', 'phone']),
        ]

    def __str__(self) -> str:
        return f"{self.name} ({self.phone})"


class Pet(models.Model):
    """반려동물 정보를 관리하는 모델"""
    DEATH_REASON_CHOICES = [
        ('natural', '자연사'),
        ('disease', '병사'),
        ('accident', '사고사'),
        ('euthanasia', '안락사'),
        ('other', '기타'),
    ]

    GENDER_CHOICES = [
        ('male', '수컷'),
        ('female', '암컷'),
    ]

    customer = models.ForeignKey(
        Customer, 
        on_delete=models.CASCADE,
        related_name='pets',
        verbose_name=_('고객')
    )
    name = models.CharField(_('반려동물명'), max_length=100)
    species = models.CharField(_('종'), max_length=50, blank=True, null=True)
    breed = models.CharField(_('품종'), max_length=100, blank=True)
    age = models.IntegerField(_('나이'), blank=True, null=True)
    weight = models.DecimalField(
        _('체중'), 
        max_digits=5, 
        decimal_places=2, 
        blank=True, 
        null=True
    )
    gender = models.CharField(
        _('성별'), 
        max_length=10, 
        choices=GENDER_CHOICES, 
        blank=True, 
        null=True
    )
    is_neutered = models.BooleanField(_('중성화 여부'), default=False)
    death_date = models.DateTimeField(_('사망일시'), blank=True, null=True)
    death_reason = models.CharField(
        _('사망사유'), 
        max_length=20, 
        choices=DEATH_REASON_CHOICES, 
        blank=True, 
        null=True
    )
    created_at = models.DateTimeField(_('생성일'), auto_now_add=True)
    updated_at = models.DateTimeField(_('수정일'), auto_now=True)

    class Meta:
        verbose_name = _('반려동물')
        verbose_name_plural = _('반려동물 목록')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['customer', 'name']),
            models.Index(fields=['death_date']),
        ]

    def __str__(self) -> str:
        return f"{self.name} ({self.species or '종류 미상'})"


class Reservation(models.Model):
    """예약 정보를 관리하는 모델"""
    STATUS_PENDING = 'pending'
    STATUS_CONFIRMED = 'confirmed'
    STATUS_IN_PROGRESS = 'in_progress'
    STATUS_COMPLETED = 'completed'
    STATUS_CANCELLED = 'cancelled'

    STATUS_CHOICES = [
        (STATUS_PENDING, '대기중'),
        (STATUS_CONFIRMED, '확정'),
        (STATUS_IN_PROGRESS, '진행중'),
        (STATUS_COMPLETED, '완료'),
        (STATUS_CANCELLED, '취소'),
    ]

    VISIT_ROUTE_CHOICES = [
        ('internet', '인터넷'),
        ('blog', '블로그'),
        ('hospital', '병원'),
        ('referral', '지인소개'),
    ]

    CANCEL_REASON_CHOICES = [
        ('customer_request', '고객 요청'),
        ('admin_cancel', '관리자 취소'),
        ('no_show', '노쇼'),
    ]

    REFUND_STATUS_CHOICES = [
        ('pending', '대기'),
        ('completed', '완료'),
        ('failed', '실패'),
    ]

    # 기본 정보
    customer = models.ForeignKey(
        Customer, 
        on_delete=models.PROTECT,
        related_name='reservations',
        verbose_name=_('고객')
    )
    pet = models.ForeignKey(
        Pet, 
        on_delete=models.PROTECT,
        related_name='reservations',
        verbose_name=_('반려동물')
    )
    package = models.ForeignKey(
        FuneralPackage, 
        on_delete=models.PROTECT,
        related_name='reservations',
        blank=True, 
        null=True,
        verbose_name=_('장례 패키지')
    )
    premium_line = models.ForeignKey(
        PremiumLine,
        on_delete=models.PROTECT,
        related_name='reservations',
        blank=True,
        null=True,
        verbose_name=_('프리미엄 라인')
    )
    additional_options = models.ManyToManyField(
        AdditionalOption,
        related_name='reservations',
        blank=True,
        verbose_name=_('추가 옵션')
    )
    memorial_room = models.ForeignKey(
        MemorialRoom, 
        on_delete=models.PROTECT,
        related_name='reservations',
        blank=True, 
        null=True,
        verbose_name=_('추모실')
    )

    # 예약 상태 및 일정
    scheduled_at = models.DateTimeField(_('예약일시'), blank=True, null=True)
    completed_at = models.DateTimeField(_('완료일시'), blank=True, null=True)
    is_blocked = models.BooleanField(_('블록 처리 여부'), default=False)
    block_end_time = models.DateTimeField(_('블록 종료 시간'), blank=True, null=True)
    status = models.CharField(
        _('상태'), 
        max_length=20, 
        choices=STATUS_CHOICES, 
        default=STATUS_PENDING
    )
    assigned_staff = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='assigned_reservations',
        blank=True,
        null=True,
        verbose_name=_('담당 직원')
    )

    # 부가 정보
    is_emergency = models.BooleanField(_('긴급여부'), default=False)
    visit_route = models.CharField(
        _('방문경로'), 
        max_length=20, 
        choices=VISIT_ROUTE_CHOICES, 
        blank=True, 
        null=True
    )
    referral_hospital = models.CharField(_('경유병원'), max_length=100, blank=True)
    need_death_certificate = models.BooleanField(_('장례확인서필요여부'), default=False)
    memo = models.TextField(_('메모'), blank=True)

    # 생성/수정 정보
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='created_reservations',
        verbose_name=_('생성자')
    )
    created_at = models.DateTimeField(_('생성일'), auto_now_add=True)
    updated_at = models.DateTimeField(_('수정일'), auto_now=True)

    # 취소 관련 정보
    cancelled_at = models.DateTimeField(_('취소일시'), null=True, blank=True)
    cancel_reason = models.CharField(
        _('취소사유'), 
        max_length=20, 
        choices=CANCEL_REASON_CHOICES, 
        null=True, 
        blank=True
    )
    cancel_notes = models.TextField(_('취소비고'), blank=True)
    penalty_amount = models.DecimalField(
        _('위약금'), 
        max_digits=10, 
        decimal_places=2, 
        null=True, 
        blank=True
    )
    refund_amount = models.DecimalField(
        _('환불금액'), 
        max_digits=10, 
        decimal_places=2, 
        null=True, 
        blank=True
    )
    refund_status = models.CharField(
        _('환불상태'), 
        max_length=20, 
        choices=REFUND_STATUS_CHOICES,
        default='pending'
    )

    # 재고 관련 필드 추가
    inventory_items = models.ManyToManyField(
        'inventory.InventoryItem',
        through='ReservationInventoryItem',
        related_name='reservations',
        verbose_name=_('사용된 재고')
    )

    class Meta:
        verbose_name = _('예약')
        verbose_name_plural = _('예약 목록')
        ordering = ['-scheduled_at']
        indexes = [
            models.Index(fields=['status', 'scheduled_at']),
            models.Index(fields=['customer', 'status']),
            models.Index(fields=['assigned_staff', 'status']),
            models.Index(fields=['is_blocked', 'block_end_time']),
            models.Index(fields=['completed_at']),
        ]

    def __str__(self) -> str:
        return f"{self.customer.name} - {self.pet.name} ({self.get_status_display()})"

    def save(self, *args, **kwargs):
        is_status_completed = False
        if self.pk:
            old_instance = Reservation.objects.get(pk=self.pk)
            if old_instance.status != self.STATUS_COMPLETED and self.status == self.STATUS_COMPLETED:
                is_status_completed = True

        super().save(*args, **kwargs)

        # 상태가 완료로 변경될 때 재고 처리
        if is_status_completed:
            self.process_inventory_usage()

    def process_inventory_usage(self):
        """예약 완료 시 사용된 재고를 처리합니다."""
        from inventory.models import StockMovement
        
        for item_usage in self.inventory_items_used.all():
            # 재고 감소 처리
            stock_movement = StockMovement.objects.create(
                item=item_usage.inventory_item,
                quantity=-item_usage.quantity,  # 음수로 처리하여 재고 감소
                movement_type='usage',
                reference_number=f'RSV-{self.id}',
                notes=f'예약 {self.id} 완료에 따른 재고 사용'
            )
            
            # 재고 수량 업데이트
            item = item_usage.inventory_item
            item.current_stock -= item_usage.quantity
            item.save()

    def calculate_penalty_amount(self) -> Decimal:
        """취소 시점에 따른 위약금을 계산합니다."""
        if not self.scheduled_at or not self.package:
            return Decimal('0')

        hours_until_reservation = self._get_hours_until_reservation()

        if hours_until_reservation >= 168:  # 7일 이상
            return Decimal('0')
        elif hours_until_reservation >= 72:  # 3-7일
            return self.package.base_price * Decimal('0.3')
        elif hours_until_reservation >= 24:  # 1-3일
            return self.package.base_price * Decimal('0.5')
        else:  # 24시간 이내
            return self.package.base_price

    def can_cancel(self) -> bool:
        """예약 취소 가능 여부를 확인합니다."""
        if self.status == self.STATUS_PENDING:
            return True
        elif self.status == self.STATUS_CONFIRMED:
            return self._get_hours_until_reservation() >= 24
        return False

    def _get_hours_until_reservation(self) -> float:
        """예약까지 남은 시간(시간)을 계산합니다."""
        if not self.scheduled_at:
            return 0.0
        return (self.scheduled_at - timezone.now()).total_seconds() / 3600


class ReservationHistory(models.Model):
    """예약 상태 변경 이력을 관리하는 모델"""
    reservation = models.ForeignKey(
        Reservation, 
        on_delete=models.CASCADE,
        related_name='histories',
        verbose_name=_('예약')
    )
    from_status = models.CharField(
        _('이전상태'), 
        max_length=20, 
        choices=Reservation.STATUS_CHOICES
    )
    to_status = models.CharField(
        _('변경상태'), 
        max_length=20, 
        choices=Reservation.STATUS_CHOICES
    )
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        verbose_name=_('처리자')
    )
    notes = models.TextField(_('비고'), blank=True)
    created_at = models.DateTimeField(_('생성일'), auto_now_add=True)

    class Meta:
        verbose_name = _('예약 이력')
        verbose_name_plural = _('예약 이력 목록')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['reservation', '-created_at']),
        ]

    def __str__(self) -> str:
        return f"{self.reservation} ({self.from_status} → {self.to_status})"


class MemorialRoom(models.Model):
    """추모실 모델"""
    ROOM_STATUS_CHOICES = [
        ('available', '사용가능'),
        ('in_use', '사용중'),
        ('reserved', '예약중'),
    ]

    name = models.CharField('추모실 이름', max_length=100)
    capacity = models.IntegerField('수용 인원', default=10)
    description = models.TextField('설명', blank=True)
    is_active = models.BooleanField('활성화 여부', default=True)
    operating_hours = models.JSONField(
        '운영 시간',
        default=dict,
        help_text='{"start_time": "HH:MM", "end_time": "HH:MM"} 형식'
    )
    current_status = models.CharField(
        '현재 상태',
        max_length=20,
        choices=ROOM_STATUS_CHOICES,
        default='available'
    )
    created_at = models.DateTimeField('생성일시', auto_now_add=True)
    updated_at = models.DateTimeField('수정일시', auto_now=True)

    class Meta:
        ordering = ['name']
        verbose_name = '추모실'
        verbose_name_plural = '추모실 목록'

    def __str__(self):
        return f"{self.name} ({self.get_current_status_display()})"


# 예약에 사용된 재고 아이템을 관리하는 중간 모델
class ReservationInventoryItem(models.Model):
    reservation = models.ForeignKey(
        Reservation,
        on_delete=models.CASCADE,
        related_name='inventory_items_used'
    )
    inventory_item = models.ForeignKey(
        'inventory.InventoryItem',
        on_delete=models.PROTECT,
        related_name='reservation_usages'
    )
    quantity = models.PositiveIntegerField(_('사용 수량'))
    created_at = models.DateTimeField(_('생성일'), auto_now_add=True)

    class Meta:
        verbose_name = _('예약 사용 재고')
        verbose_name_plural = _('예약 사용 재고 목록')
        unique_together = ['reservation', 'inventory_item']

    def __str__(self):
        return f"{self.reservation} - {self.inventory_item} ({self.quantity}개)"
