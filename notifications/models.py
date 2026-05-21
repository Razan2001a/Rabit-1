"""
RABIT — Notifications Models
نظام الإشعارات الداخلية للمنصة.
"""
from django.db import models
from django.utils import timezone


class Notification(models.Model):
    """إشعار يصل للمستخدم عند حدث مهم (طلب جديد، رسالة، اعتماد ملف…)."""

    class Kind(models.TextChoices):
        INFO       = 'info',       'معلوماتي'
        REQUEST    = 'request',    'طلب جديد'
        MESSAGE    = 'message',    'رسالة'
        APPROVAL   = 'approval',   'اعتماد'
        REJECTION  = 'rejection',  'رفض'
        PAYMENT    = 'payment',    'دفع'
        DEAL       = 'deal',       'صفقة'

    user      = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='notifications')
    kind      = models.CharField(max_length=20, choices=Kind.choices, default=Kind.INFO)
    title     = models.CharField(max_length=200, verbose_name='العنوان')
    body      = models.TextField(blank=True, verbose_name='التفاصيل')
    link      = models.CharField(max_length=300, blank=True, verbose_name='رابط')
    is_read   = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        verbose_name = 'إشعار'
        verbose_name_plural = 'الإشعارات'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user} — {self.title}'

    @classmethod
    def notify(cls, user, title, body='', kind='info', link=''):
        """دالة سريعة لإرسال إشعار."""
        return cls.objects.create(
            user=user, title=title, body=body, kind=kind, link=link
        )
