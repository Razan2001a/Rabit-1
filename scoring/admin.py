from django.contrib import admin
from .models import AdvisorRating, StartupScore


@admin.register(AdvisorRating)
class AdvisorRatingAdmin(admin.ModelAdmin):
    list_display = ('advisor', 'startup', 'score', 'created_at')
    list_filter  = ('score',)


@admin.register(StartupScore)
class StartupScoreAdmin(admin.ModelAdmin):
    list_display = ('startup', 'total_score', 'updated_at')
    readonly_fields = ('startup', 'updated_at')
    fields = (
        'startup',
        'score_basic', 'score_verified', 'score_docs',
        'score_financial', 'score_story', 'score_team',
        'score_activity', 'score_video', 'score_website',
        'admin_notes', 'updated_at',
    )

    @admin.display(description='المجموع / 100')
    def total_score(self, obj):
        return obj.calculate()
