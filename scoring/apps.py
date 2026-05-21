from django.apps import AppConfig


class ScoringConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'scoring'
    verbose_name = 'التقييم والـ Scorecard'

    def ready(self):
        import scoring.signals  # noqa: F401
