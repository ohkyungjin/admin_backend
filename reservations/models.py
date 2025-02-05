from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from funeral.models import FuneralPackage


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
    ]

    GENDER_CHOICES = [
        ('male', '수컷'),
        ('female', '암컷'),
    ]

    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='pets')
    name = models.CharField(_('반려동물명'), max_length=100)
    species = models.CharField(_('종'), max_length=50)
    breed = models.CharField(_('품종'), max_length=100, blank=True)
    age = models.IntegerField(_('나이'))
    weight = models.DecimalField(_('체중'), max_digits=5, decimal_places=2)
    gender = models.CharField(_('성별'), max_length=10, choices=GENDER_CHOICES, default='male')
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


class MemorialRoom(models.Model):
    name = models.CharField(_('추모실명'), max_length=100)
    capacity = models.IntegerField(_('수용인원'))
    description = models.TextField(_('설명'), blank=True)
    is_active = models.BooleanField(_('사용가능여부'), default=True)
    created_at = models.DateTimeField(_('생성일'), auto_now_add=True)
    updated_at = models.DateTimeField(_('수정일'), auto_now=True)

    class Meta:
        verbose_name = _('추모실')
        verbose_name_plural = _('추모실 목록')
        ordering = ['name']

    def __str__(self):
        return self.name


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

    customer = models.ForeignKey(Customer, on_delete=models.PROTECT, related_name='reservations')
    pet = models.ForeignKey(Pet, on_delete=models.PROTECT, related_name='reservations')
    package = models.ForeignKey(FuneralPackage, on_delete=models.PROTECT, related_name='reservations')
    memorial_room = models.ForeignKey(MemorialRoom, on_delete=models.PROTECT, related_name='reservations')
    scheduled_at = models.DateTimeField(_('예약일시'))
    status = models.CharField(_('상태'), max_length=20, choices=STATUS_CHOICES, default='pending')
    assigned_staff = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='assigned_reservations'
    )
    is_emergency = models.BooleanField(_('긴급여부'), default=False)
    visit_route = models.CharField(_('방문경로'), max_length=20, choices=VISIT_ROUTE_CHOICES)
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
