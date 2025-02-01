from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils.translation import gettext_lazy as _


class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError(_('이메일은 필수입니다.'))
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('auth_level', 3)

        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('Superuser must have is_staff=True.'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('Superuser must have is_superuser=True.'))

        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    # 권한 레벨 상수 정의
    LEVEL_SUPERADMIN = 3
    LEVEL_ADMIN = 2
    LEVEL_INSTRUCTOR = 1

    AUTH_LEVEL_CHOICES = [
        (LEVEL_INSTRUCTOR, '지도사'),
        (LEVEL_ADMIN, '관리자'),
        (LEVEL_SUPERADMIN, '슈퍼관리자'),
    ]

    email = models.EmailField(_('이메일'), unique=True)
    name = models.CharField(_('이름'), max_length=50)
    phone = models.CharField(_('전화번호'), max_length=20)
    auth_level = models.IntegerField(
        _('권한 레벨'),
        choices=AUTH_LEVEL_CHOICES,
        default=LEVEL_INSTRUCTOR,
        help_text=_('1: 지도사, 2: 관리자, 3: 슈퍼관리자')
    )
    department = models.CharField(_('부서'), max_length=50, blank=True)
    position = models.CharField(_('직책'), max_length=50, blank=True)
    last_password_change = models.DateTimeField(_('마지막 비밀번호 변경일'), auto_now_add=True)
    is_active = models.BooleanField(_('활성화 여부'), default=True)
    is_staff = models.BooleanField(_('스태프 여부'), default=False)
    created_at = models.DateTimeField(_('생성일'), auto_now_add=True)
    updated_at = models.DateTimeField(_('수정일'), auto_now=True)

    groups = models.ManyToManyField(
        'auth.Group',
        verbose_name=_('groups'),
        blank=True,
        help_text=_('The groups this user belongs to.'),
        related_name='custom_user_groups',
        related_query_name='custom_user'
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        verbose_name=_('user permissions'),
        blank=True,
        help_text=_('Specific permissions for this user.'),
        related_name='custom_user_permissions',
        related_query_name='custom_user'
    )

    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['name', 'phone']

    class Meta:
        verbose_name = _('직원')
        verbose_name_plural = _('직원 목록')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.email})"


class ActivityLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='activity_logs')
    action_type = models.CharField(_('작업 유형'), max_length=50)
    description = models.TextField(_('상세 내용'))
    ip_address = models.GenericIPAddressField(_('IP 주소'))
    action_time = models.DateTimeField(_('작업 시간'), auto_now_add=True)
    created_at = models.DateTimeField(_('생성일'), auto_now_add=True)

    class Meta:
        verbose_name = _('활동 로그')
        verbose_name_plural = _('활동 로그 목록')
        ordering = ['-action_time']

    def __str__(self):
        return f"{self.user.name} - {self.action_type} ({self.action_time})"
