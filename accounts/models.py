"""
RABIT — Accounts Models
نظام المستخدمين مع الأدوار + التحقق من البريد
(الـ Profiles الخاصة بكل دور موجودة في تطبيق profiles)
"""
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone


class User(AbstractUser):
    """نموذج المستخدم المخصص مع نظام الأدوار."""

    class Role(models.TextChoices):
        STARTUP  = 'startup',  'شركة ناشئة'
        INVESTOR = 'investor', 'مستثمر'
        ADVISOR  = 'advisor',  'مستشار'
        ADMIN    = 'admin',    'إدارة'

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.STARTUP,
        verbose_name='الدور',
    )
    phone = models.CharField(max_length=20, blank=True, verbose_name='رقم الهاتف')
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True, verbose_name='الصورة الشخصية')
    is_verified = models.BooleanField(default=False, verbose_name='موثق')
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        verbose_name = 'مستخدم'
        verbose_name_plural = 'المستخدمون'

    def __str__(self):
        return f'{self.get_full_name() or self.username} ({self.get_role_display()})'

    def get_dashboard_url(self):
        urls = {
            self.Role.STARTUP:  '/dashboard/startup/',
            self.Role.INVESTOR: '/dashboard/investor/',
            self.Role.ADVISOR:  '/dashboard/advisor/',
            self.Role.ADMIN:    '/admin/',
        }
        return urls.get(self.role, '/')

    @property
    def is_startup(self):
        return self.role == self.Role.STARTUP

    @property
    def is_investor(self):
        return self.role == self.Role.INVESTOR

    @property
    def is_advisor(self):
        return self.role == self.Role.ADVISOR

    @property
    def is_admin(self):
        return self.role == self.Role.ADMIN or self.is_superuser


class EmailVerificationCode(models.Model):
    """رمز التحقق من البريد الإلكتروني — 6 أرقام، صالح 10 دقائق."""
    user       = models.OneToOneField(User, on_delete=models.CASCADE, related_name='verification_code')
    code       = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    def is_expired(self):
        return timezone.now() > self.expires_at

    def __str__(self):
        return f'{self.user.email} — {self.code}'

    class Meta:
        verbose_name = 'رمز تحقق'
        verbose_name_plural = 'رموز التحقق'
