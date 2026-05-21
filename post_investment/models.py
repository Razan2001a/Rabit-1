"""
RABIT — Post-Investment Models
- PeriodicReport: تقارير دورية للمستثمرين بعد إغلاق الصفقة
- BoardMeeting: اجتماعات مجلس الإدارة
- KPISnapshot: مؤشرات أداء دورية
"""
from django.db import models
from django.utils import timezone


class PeriodicReport(models.Model):
    """تقرير دوري (شهري/ربعي/سنوي) ترسله الشركة لمستثمريها."""

    class Period(models.TextChoices):
        MONTHLY   = 'monthly',   'شهري'
        QUARTERLY = 'quarterly', 'ربعي'
        YEARLY    = 'yearly',    'سنوي'

    startup    = models.ForeignKey('profiles.StartupProfile', on_delete=models.CASCADE, related_name='ir_reports')
    title      = models.CharField(max_length=200, verbose_name='عنوان التقرير')
    period     = models.CharField(max_length=20, choices=Period.choices, default=Period.QUARTERLY)
    summary    = models.TextField(verbose_name='ملخص تنفيذي')
    revenue    = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True, verbose_name='الإيرادات')
    burn_rate  = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True, verbose_name='Burn Rate')
    runway_months = models.PositiveSmallIntegerField(default=0, verbose_name='Runway (شهور)')
    customers_count = models.PositiveIntegerField(default=0, verbose_name='عدد العملاء')
    team_size  = models.PositiveSmallIntegerField(default=0)
    achievements = models.TextField(blank=True, verbose_name='الإنجازات')
    challenges = models.TextField(blank=True, verbose_name='التحديات')
    file       = models.FileField(upload_to='ir/reports/', blank=True, null=True, verbose_name='ملف التقرير (PDF)')
    sent_at    = models.DateTimeField(default=timezone.now)
    period_start = models.DateField(null=True, blank=True)
    period_end   = models.DateField(null=True, blank=True)

    class Meta:
        verbose_name = 'تقرير دوري'
        verbose_name_plural = 'التقارير الدورية'
        ordering = ['-sent_at']

    def __str__(self):
        return f'{self.title} — {self.startup}'


class BoardMeeting(models.Model):
    """اجتماع مجلس إدارة."""
    startup      = models.ForeignKey('profiles.StartupProfile', on_delete=models.CASCADE, related_name='board_meetings')
    title        = models.CharField(max_length=200)
    scheduled_at = models.DateTimeField()
    location     = models.CharField(max_length=200, blank=True, verbose_name='المكان / رابط Zoom')
    agenda       = models.TextField(blank=True)
    minutes      = models.TextField(blank=True, verbose_name='محضر الاجتماع')

    class Meta:
        verbose_name = 'اجتماع مجلس إدارة'
        verbose_name_plural = 'اجتماعات مجلس الإدارة'
        ordering = ['-scheduled_at']

    def __str__(self):
        return self.title


class KPISnapshot(models.Model):
    """نقطة قياس KPIs بتاريخ معيّن."""
    startup        = models.ForeignKey('profiles.StartupProfile', on_delete=models.CASCADE, related_name='kpi_snapshots')
    snapshot_date  = models.DateField(default=timezone.now)
    mrr            = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, verbose_name='MRR')
    arr            = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, verbose_name='ARR')
    cac            = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name='CAC')
    ltv            = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name='LTV')
    churn_pct      = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, verbose_name='Churn %')
    notes          = models.TextField(blank=True)

    class Meta:
        verbose_name = 'KPI Snapshot'
        verbose_name_plural = 'KPI Snapshots'
        ordering = ['-snapshot_date']

    def __str__(self):
        return f'{self.startup} — {self.snapshot_date}'
