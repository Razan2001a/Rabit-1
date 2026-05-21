from django.contrib import admin
from .models import PeriodicReport, BoardMeeting, KPISnapshot


@admin.register(PeriodicReport)
class PeriodicReportAdmin(admin.ModelAdmin):
    list_display = ('title', 'startup', 'period', 'sent_at')
    list_filter  = ('period',)


@admin.register(BoardMeeting)
class BoardMeetingAdmin(admin.ModelAdmin):
    list_display = ('title', 'startup', 'scheduled_at')


@admin.register(KPISnapshot)
class KPISnapshotAdmin(admin.ModelAdmin):
    list_display = ('startup', 'snapshot_date', 'mrr', 'arr', 'churn_pct')
