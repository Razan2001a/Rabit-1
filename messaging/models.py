"""RABIT — Messaging Models"""
from django.db import models
from django.utils import timezone


class Conversation(models.Model):
    """محادثة مرتبطة بطلب استثمار مقبول (شركة ناشئة ↔ مستثمر)."""
    request = models.OneToOneField(
        'deals.InvestorRequest',
        on_delete=models.CASCADE,
        related_name='conversation',
    )
    created_at = models.DateTimeField(default=timezone.now)
    is_closed  = models.BooleanField(default=False)

    class Meta:
        verbose_name = 'محادثة'
        ordering = ['-created_at']

    def __str__(self):
        return f'محادثة #{self.pk}'

    @property
    def participants(self):
        return {
            'investor': self.request.investor,
            'startup':  self.request.startup.user,
        }


class Message(models.Model):
    """رسالة داخل محادثة الإغلاق — نقاش فقط بلا بيانات حساسة."""
    conversation   = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    sender         = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='sent_messages')
    content        = models.TextField()
    sent_at        = models.DateTimeField(default=timezone.now)
    is_read        = models.BooleanField(default=False)
    is_blocked     = models.BooleanField(default=False, verbose_name='محجوبة (بيانات حساسة)')
    blocked_reason = models.CharField(max_length=300, blank=True, verbose_name='سبب الحجب')

    class Meta:
        verbose_name = 'رسالة'
        ordering = ['sent_at']


class SharedDataRoomFile(models.Model):
    """ملف Data Room يُضاف للنقاش داخل محادثة إغلاق."""
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='shared_files')
    shared_by    = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='shared_dr_files')
    dr_file      = models.ForeignKey('data_room.DataRoomFile', on_delete=models.CASCADE, related_name='shared_in_chats')
    shared_at    = models.DateTimeField(default=timezone.now)
    note         = models.CharField(max_length=300, blank=True, verbose_name='ملاحظة')

    class Meta:
        verbose_name        = 'ملف مشارك'
        verbose_name_plural = 'ملفات مشاركة'
        ordering = ['-shared_at']

    def __str__(self):
        return f'{self.dr_file.name} → محادثة #{self.conversation_id}'


# ─────────────────────────────────────────────────────────────
# PITCH SESSIONS
# ─────────────────────────────────────────────────────────────

class PitchSession(models.Model):
    """جلسة Pitch مجدولة بين مستثمر وشركة ناشئة."""

    class Status(models.TextChoices):
        REQUESTED = 'requested', 'مطلوبة'
        SCHEDULED = 'scheduled', 'مُجدولة'
        DONE      = 'done',      'مكتملة'
        CANCELLED = 'cancelled', 'مُلغاة'

    startup      = models.ForeignKey('profiles.StartupProfile', on_delete=models.CASCADE, related_name='pitch_sessions')
    investor     = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='pitch_sessions')
    requested_at = models.DateTimeField(default=timezone.now)
    scheduled_at = models.DateTimeField(null=True, blank=True, verbose_name='موعد الجلسة')
    duration_min = models.PositiveSmallIntegerField(default=30, verbose_name='المدة (دقيقة)')
    meeting_link = models.URLField(blank=True, verbose_name='رابط الاجتماع')
    agenda       = models.TextField(blank=True, verbose_name='جدول الأعمال')
    notes        = models.TextField(blank=True)
    status       = models.CharField(max_length=20, choices=Status.choices, default=Status.REQUESTED)

    class Meta:
        verbose_name        = 'جلسة Pitch'
        verbose_name_plural = 'جلسات Pitch'
        ordering = ['-scheduled_at', '-requested_at']

    def __str__(self):
        return f'Pitch — {self.startup} مع {self.investor}'


# ─────────────────────────────────────────────────────────────
# ADVISOR CONVERSATIONS  (مستثمر ↔ مستشار)
# ─────────────────────────────────────────────────────────────

class AdvisorConversation(models.Model):
    """محادثة مباشرة بين مستثمر ومستشار."""

    class PaymentStatus(models.TextChoices):
        UNPAID = 'unpaid', 'لم يُدفع'
        PAID   = 'paid',   'مدفوع'

    investor       = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='advisor_conversations')
    advisor        = models.ForeignKey('profiles.AdvisorProfile', on_delete=models.CASCADE, related_name='investor_conversations')
    service_type   = models.CharField(max_length=50, blank=True, verbose_name='الخدمة المطلوبة')
    service_name   = models.CharField(max_length=200, blank=True, verbose_name='اسم الخدمة')
    payment_status = models.CharField(max_length=10, choices=PaymentStatus.choices, default=PaymentStatus.UNPAID)
    amount         = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    created_at     = models.DateTimeField(default=timezone.now)
    is_closed      = models.BooleanField(default=False)

    class Meta:
        verbose_name    = 'محادثة مع مستشار (مستثمر)'
        unique_together = ('investor', 'advisor', 'service_type')

    def __str__(self):
        return f'{self.investor} ↔ {self.advisor} ({self.service_type})'


class AdvisorMessage(models.Model):
    """رسالة داخل محادثة مستثمر ↔ مستشار."""
    conversation   = models.ForeignKey(AdvisorConversation, on_delete=models.CASCADE, related_name='messages')
    sender         = models.ForeignKey('accounts.User', on_delete=models.CASCADE)
    content        = models.TextField()
    sent_at        = models.DateTimeField(default=timezone.now)
    is_read        = models.BooleanField(default=False)
    is_blocked     = models.BooleanField(default=False, verbose_name='محجوبة')
    blocked_reason = models.CharField(max_length=300, blank=True)

    class Meta:
        ordering = ['sent_at']


# ─────────────────────────────────────────────────────────────
# STARTUP ↔ ADVISOR CONVERSATION  (شركة ناشئة ↔ مستشار)
# ─────────────────────────────────────────────────────────────

class StartupAdvisorConversation(models.Model):
    """محادثة بين شركة ناشئة ومستشار."""

    class PaymentStatus(models.TextChoices):
        UNPAID = 'unpaid', 'لم يُدفع'
        PAID   = 'paid',   'مدفوع'

    startup         = models.ForeignKey('profiles.StartupProfile', on_delete=models.CASCADE, related_name='advisor_conversations')
    advisor         = models.ForeignKey('profiles.AdvisorProfile', on_delete=models.CASCADE, related_name='startup_conversations')
    service_request = models.ForeignKey(
        'advisory.ServiceRequest',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='conversation',
    )
    payment_status = models.CharField(max_length=10, choices=PaymentStatus.choices, default=PaymentStatus.UNPAID)
    created_at     = models.DateTimeField(default=timezone.now)
    is_closed      = models.BooleanField(default=False)

    class Meta:
        verbose_name    = 'محادثة شركة ↔ مستشار'
        unique_together = ('startup', 'advisor')

    def __str__(self):
        return f'{self.startup} ↔ {self.advisor}'


class StartupAdvisorMessage(models.Model):
    """رسالة داخل محادثة شركة ناشئة ↔ مستشار."""
    conversation   = models.ForeignKey(StartupAdvisorConversation, on_delete=models.CASCADE, related_name='messages')
    sender         = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='startup_advisor_messages')
    content        = models.TextField()
    sent_at        = models.DateTimeField(default=timezone.now)
    is_read        = models.BooleanField(default=False)
    is_blocked     = models.BooleanField(default=False, verbose_name='محجوبة')
    blocked_reason = models.CharField(max_length=300, blank=True)

    class Meta:
        ordering = ['sent_at']