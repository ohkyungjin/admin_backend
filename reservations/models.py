from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from funeral.models import FuneralPackage
from memorial_rooms.models import MemorialRoom
from django.utils import timezone
from decimal import Decimal


class Customer(models.Model):
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

    def __str__(self):
        return f"{self.name} ({self.phone})"


class Pet(models.Model):
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

    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='pets')
    name = models.CharField(_('반려동물명'), max_length=100)
    species = models.CharField(_('종'), max_length=50, blank=True, null=True)
    breed = models.CharField(_('품종'), max_length=100, blank=True)
    age = models.IntegerField(_('나이'), blank=True, null=True)
    weight = models.DecimalField(_('체중'), max_digits=5, decimal_places=2, blank=True, null=True)
    gender = models.CharField(_('성별'), max_length=10, choices=GENDER_CHOICES, blank=True, null=True)
    is_neutered = models.BooleanField(_('중성화 여부'), default=False)
    death_date = models.DateTimeField(_('사망일시'), blank=True, null=True)
    death_reason = models.CharField(_('사망사유'), max_length=20, choices=DEATH_REASON_CHOICES, blank=True, null=True)
    special_notes = models.TextField(_('특이사항'), blank=True)
    created_at = models.DateTimeField(_('생성일'), auto_now_add=True)
    updated_at = models.DateTimeField(_('수정일'), auto_now=True)

    class Meta:
        verbose_name = _('반려동물')
        verbose_name_plural = _('반려동물 목록')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.species})"


class Reservation(models.Model):
    STATUS_CHOICES = [
        ('pending', '대기중'),
        ('confirmed', '확정'),
        ('in_progress', '진행중'),
        ('completed', '완료'),
        ('cancelled', '취소'),
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

    customer = models.ForeignKey(Customer, on_delete=models.PROTECT, related_name='reservations')
    pet = models.ForeignKey(Pet, on_delete=models.PROTECT, related_name='reservations')
    package = models.ForeignKey(FuneralPackage, on_delete=models.PROTECT, related_name='reservations', blank=True, null=True)
    memorial_room = models.ForeignKey(MemorialRoom, on_delete=models.PROTECT, related_name='reservations', blank=True, null=True)
    scheduled_at = models.DateTimeField(_('예약일시'), blank=True, null=True)
    status = models.CharField(_('상태'), max_length=20, choices=STATUS_CHOICES, default='pending')
    assigned_staff = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='assigned_reservations',
        blank=True,
        null=True
    )
    is_emergency = models.BooleanField(_('긴급여부'), default=False)
    visit_route = models.CharField(_('방문경로'), max_length=20, choices=VISIT_ROUTE_CHOICES, blank=True, null=True)
    referral_hospital = models.CharField(_('경유병원'), max_length=100, blank=True)
    need_death_certificate = models.BooleanField(_('장례확인서필요여부'), default=False)
    custom_requests = models.TextField(_('요청사항'), blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='created_reservations'
    )
    created_at = models.DateTimeField(_('생성일'), auto_now_add=True)
    updated_at = models.DateTimeField(_('수정일'), auto_now=True)

    # 취소 관련 필드 추가
    cancelled_at = models.DateTimeField(_('취소일시'), null=True, blank=True)
    cancel_reason = models.CharField(_('취소사유'), max_length=20, choices=CANCEL_REASON_CHOICES, null=True, blank=True)
    cancel_notes = models.TextField(_('취소비고'), blank=True)
    penalty_amount = models.DecimalField(_('위약금'), max_digits=10, decimal_places=2, null=True, blank=True)
    refund_amount = models.DecimalField(_('환불금액'), max_digits=10, decimal_places=2, null=True, blank=True)
    refund_status = models.CharField(_('환불상태'), max_length=20, default='pending', choices=[
        ('pending', '대기'),
        ('completed', '완료'),
        ('failed', '실패'),
    ])

    class Meta:
        verbose_name = _('예약')
        verbose_name_plural = _('예약 목록')
        ordering = ['-scheduled_at']
        indexes = [
            models.Index(fields=['status', 'scheduled_at']),
            models.Index(fields=['customer', 'status']),
        ]

    def __str__(self):
        return f"{self.customer.name} - {self.pet.name} ({self.get_status_display()})"

    def calculate_penalty_amount(self):
        """취소 시점에 따른 위약금을 계산합니다."""
        if not self.scheduled_at or not self.package:
            return 0

        now = timezone.now()
        hours_until_reservation = (self.scheduled_at - now).total_seconds() / 3600

        if hours_until_reservation >= 168:  # 7일 이상
            return 0
        elif hours_until_reservation >= 72:  # 3-7일
            return self.package.base_price * Decimal('0.3')
        elif hours_until_reservation >= 24:  # 1-3일
            return self.package.base_price * Decimal('0.5')
        else:  # 24시간 이내
            return self.package.base_price

    def can_cancel(self):
        """예약 취소 가능 여부를 확인합니다."""
        if self.status == 'pending':
            return True
        elif self.status == 'confirmed':
            hours_until_reservation = (self.scheduled_at - timezone.now()).total_seconds() / 3600
            return hours_until_reservation >= 24
        return False


class ReservationHistory(models.Model):
    reservation = models.ForeignKey(Reservation, on_delete=models.CASCADE, related_name='histories')
    from_status = models.CharField(_('이전상태'), max_length=20, choices=Reservation.STATUS_CHOICES)
    to_status = models.CharField(_('변경상태'), max_length=20, choices=Reservation.STATUS_CHOICES)
    changed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    notes = models.TextField(_('비고'), blank=True)
    created_at = models.DateTimeField(_('생성일'), auto_now_add=True)

    class Meta:
        verbose_name = _('예약 이력')
        verbose_name_plural = _('예약 이력 목록')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.reservation} ({self.from_status} → {self.to_status})"
