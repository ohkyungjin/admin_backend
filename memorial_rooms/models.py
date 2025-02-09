from django.db import models
from django.utils.translation import gettext_lazy as _


class MemorialRoom(models.Model):
    name = models.CharField(_('추모실명'), max_length=100)
    capacity = models.IntegerField(_('수용인원'), blank=True, null=True)
    operating_hours = models.CharField(_('이용시간'), max_length=100, help_text='예: 09:00-18:00')
    notes = models.TextField(_('특이사항'), blank=True)
    is_active = models.BooleanField(_('사용가능여부'), default=True)
    created_at = models.DateTimeField(_('생성일'), auto_now_add=True)
    updated_at = models.DateTimeField(_('수정일'), auto_now=True)

    class Meta:
        verbose_name = _('추모실')
        verbose_name_plural = _('추모실 목록')
        ordering = ['name']

    def __str__(self):
        return self.name
