from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings


class Category(models.Model):
    name = models.CharField(_('카테고리명'), max_length=50)
    description = models.TextField(_('설명'), blank=True)
    created_at = models.DateTimeField(_('생성일'), auto_now_add=True)
    updated_at = models.DateTimeField(_('수정일'), auto_now=True)

    class Meta:
        verbose_name = _('카테고리')
        verbose_name_plural = _('카테고리 목록')
        ordering = ['name']

    def __str__(self):
        return self.name


class Supplier(models.Model):
    name = models.CharField(_('공급업체명'), max_length=100)
    contact_name = models.CharField(_('담당자명'), max_length=50)
    phone = models.CharField(_('전화번호'), max_length=20)
    email = models.EmailField(_('이메일'), blank=True)
    address = models.TextField(_('주소'), blank=True)
    created_at = models.DateTimeField(_('생성일'), auto_now_add=True)
    updated_at = models.DateTimeField(_('수정일'), auto_now=True)

    class Meta:
        verbose_name = _('공급업체')
        verbose_name_plural = _('공급업체 목록')
        ordering = ['name']

    def __str__(self):
        return self.name


class InventoryItem(models.Model):
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name='items')
    supplier = models.ForeignKey(Supplier, on_delete=models.PROTECT, related_name='items')
    name = models.CharField(_('품목명'), max_length=100)
    code = models.CharField(_('품목코드'), max_length=50, unique=True)
    description = models.TextField(_('설명'), blank=True)
    unit = models.CharField(_('단위'), max_length=20)
    unit_price = models.DecimalField(_('단가'), max_digits=10, decimal_places=2)
    current_stock = models.IntegerField(_('현재 재고'), default=0)
    minimum_stock = models.IntegerField(_('최소 재고'), default=0)
    maximum_stock = models.IntegerField(_('최대 재고'), default=0)
    created_at = models.DateTimeField(_('생성일'), auto_now_add=True)
    updated_at = models.DateTimeField(_('수정일'), auto_now=True)

    class Meta:
        verbose_name = _('재고 품목')
        verbose_name_plural = _('재고 품목 목록')
        ordering = ['category', 'name']
        indexes = [
            models.Index(fields=['code']),
            models.Index(fields=['category', 'name']),
        ]

    def __str__(self):
        return f"{self.name} ({self.code})"


class StockMovement(models.Model):
    MOVEMENT_TYPES = [
        ('in', '입고'),
        ('out', '출고'),
        ('adjust', '조정'),
        ('return', '반품'),
    ]

    item = models.ForeignKey(InventoryItem, on_delete=models.PROTECT, related_name='movements')
    movement_type = models.CharField(_('이동 유형'), max_length=10, choices=MOVEMENT_TYPES)
    quantity = models.IntegerField(_('수량'))
    unit_price = models.DecimalField(_('단가'), max_digits=10, decimal_places=2)
    reference_number = models.CharField(_('참조번호'), max_length=50, blank=True)
    notes = models.TextField(_('비고'), blank=True)
    employee = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='stock_movements')
    created_at = models.DateTimeField(_('생성일'), auto_now_add=True)

    class Meta:
        verbose_name = _('재고 이동')
        verbose_name_plural = _('재고 이동 목록')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['movement_type', 'created_at']),
            models.Index(fields=['item', 'created_at']),
        ]

    def __str__(self):
        return f"{self.get_movement_type_display()} - {self.item.name} ({self.quantity})"


class PurchaseOrder(models.Model):
    ORDER_STATUS = [
        ('draft', '임시저장'),
        ('pending', '승인대기'),
        ('approved', '승인완료'),
        ('ordered', '발주완료'),
        ('received', '입고완료'),
        ('cancelled', '취소'),
    ]

    supplier = models.ForeignKey(Supplier, on_delete=models.PROTECT, related_name='purchase_orders')
    order_number = models.CharField(_('발주번호'), max_length=50, unique=True)
    status = models.CharField(_('상태'), max_length=20, choices=ORDER_STATUS, default='draft')
    order_date = models.DateField(_('발주일'), null=True, blank=True)
    expected_date = models.DateField(_('입고예정일'), null=True, blank=True)
    total_amount = models.DecimalField(_('총 금액'), max_digits=12, decimal_places=2, default=0)
    notes = models.TextField(_('비고'), blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='created_orders')
    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True, related_name='approved_orders')
    created_at = models.DateTimeField(_('생성일'), auto_now_add=True)
    updated_at = models.DateTimeField(_('수정일'), auto_now=True)

    class Meta:
        verbose_name = _('발주서')
        verbose_name_plural = _('발주서 목록')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['order_number']),
            models.Index(fields=['status', 'order_date']),
        ]

    def __str__(self):
        return f"{self.order_number} ({self.get_status_display()})"


class PurchaseOrderItem(models.Model):
    order = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE, related_name='items')
    item = models.ForeignKey(InventoryItem, on_delete=models.PROTECT, related_name='order_items')
    quantity = models.IntegerField(_('수량'))
    unit_price = models.DecimalField(_('단가'), max_digits=10, decimal_places=2)
    total_price = models.DecimalField(_('합계'), max_digits=12, decimal_places=2)
    received_quantity = models.IntegerField(_('입고수량'), default=0)
    notes = models.TextField(_('비고'), blank=True)

    class Meta:
        verbose_name = _('발주 품목')
        verbose_name_plural = _('발주 품목 목록')
        ordering = ['id']

    def __str__(self):
        return f"{self.item.name} ({self.quantity})"
