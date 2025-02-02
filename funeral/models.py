from django.db import models
from django.utils.translation import gettext_lazy as _


class FuneralPackage(models.Model):
    """기본 장례 패키지"""
    name = models.CharField(_('패키지명'), max_length=100)
    description = models.TextField(_('설명'))
    base_price = models.DecimalField(_('기본 가격'), max_digits=10, decimal_places=2)
    is_active = models.BooleanField(_('활성화 여부'), default=True)
    created_at = models.DateTimeField(_('생성일'), auto_now_add=True)
    updated_at = models.DateTimeField(_('수정일'), auto_now=True)

    class Meta:
        verbose_name = _('장례 패키지')
        verbose_name_plural = _('장례 패키지 목록')
        ordering = ['name']

    def __str__(self):
        return self.name


class PackageItem(models.Model):
    """패키지에 포함된 카테고리별 기본 구성 품목"""
    package = models.ForeignKey('FuneralPackage', on_delete=models.CASCADE, related_name='items')
    category = models.ForeignKey('inventory.Category', on_delete=models.PROTECT)
    default_item = models.ForeignKey('inventory.InventoryItem', on_delete=models.PROTECT)
    is_required = models.BooleanField(_('필수 여부'), default=True)
    created_at = models.DateTimeField(_('생성일'), auto_now_add=True)
    updated_at = models.DateTimeField(_('수정일'), auto_now=True)

    class Meta:
        verbose_name = _('패키지 구성 품목')
        verbose_name_plural = _('패키지 구성 품목 목록')
        unique_together = ['package', 'category']

    def __str__(self):
        return f"{self.package.name} - {self.category.name}"


class PackageItemOption(models.Model):
    """각 카테고리별 선택 가능한 품목 옵션"""
    package_item = models.ForeignKey('PackageItem', on_delete=models.CASCADE, related_name='options')
    item = models.ForeignKey('inventory.InventoryItem', on_delete=models.PROTECT)
    additional_price = models.DecimalField(_('추가 가격'), max_digits=10, decimal_places=2, default=0)
    is_active = models.BooleanField(_('활성화 여부'), default=True)
    created_at = models.DateTimeField(_('생성일'), auto_now_add=True)
    updated_at = models.DateTimeField(_('수정일'), auto_now=True)

    class Meta:
        verbose_name = _('패키지 품목 옵션')
        verbose_name_plural = _('패키지 품목 옵션 목록')
        ordering = ['additional_price']

    def __str__(self):
        return f"{self.package_item} - {self.item.name}"


class PremiumLine(models.Model):
    """프리미엄 라인 패키지"""
    name = models.CharField(_('프리미엄 라인명'), max_length=100)
    description = models.TextField(_('설명'))
    price = models.DecimalField(_('가격'), max_digits=10, decimal_places=2)
    is_active = models.BooleanField(_('활성화 여부'), default=True)
    created_at = models.DateTimeField(_('생성일'), auto_now_add=True)
    updated_at = models.DateTimeField(_('수정일'), auto_now=True)

    class Meta:
        verbose_name = _('프리미엄 라인')
        verbose_name_plural = _('프리미엄 라인 목록')
        ordering = ['price']

    def __str__(self):
        return self.name


class PremiumLineItem(models.Model):
    """프리미엄 라인 구성 품목"""
    premium_line = models.ForeignKey('PremiumLine', on_delete=models.CASCADE, related_name='items')
    category = models.ForeignKey('inventory.Category', on_delete=models.PROTECT)
    item = models.ForeignKey('inventory.InventoryItem', on_delete=models.PROTECT)
    created_at = models.DateTimeField(_('생성일'), auto_now_add=True)
    updated_at = models.DateTimeField(_('수정일'), auto_now=True)

    class Meta:
        verbose_name = _('프리미엄 라인 구성 품목')
        verbose_name_plural = _('프리미엄 라인 구성 품목 목록')
        unique_together = ['premium_line', 'category']

    def __str__(self):
        return f"{self.premium_line.name} - {self.item.name}"


class AdditionalOption(models.Model):
    """추가 선택 가능한 옵션"""
    name = models.CharField(_('옵션명'), max_length=100)
    description = models.TextField(_('설명'))
    price = models.DecimalField(_('가격'), max_digits=10, decimal_places=2)
    category = models.ForeignKey('inventory.Category', on_delete=models.PROTECT, null=True, blank=True)
    is_active = models.BooleanField(_('활성화 여부'), default=True)
    created_at = models.DateTimeField(_('생성일'), auto_now_add=True)
    updated_at = models.DateTimeField(_('수정일'), auto_now=True)

    class Meta:
        verbose_name = _('추가 옵션')
        verbose_name_plural = _('추가 옵션 목록')
        ordering = ['name']

    def __str__(self):
        return self.name
