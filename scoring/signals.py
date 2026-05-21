"""
إعادة حساب StartupScore تلقائياً عند حفظ StartupProfile أو رفع وثيقة.
"""
from django.db.models.signals import post_save
from django.dispatch import receiver


def _refresh_score(startup):
    """حساب النقاط وتحديث scorecard مباشرةً بـ update() لتجنب الحلقة اللانهائية."""
    try:
        from .models import StartupScore
        from profiles.models import StartupProfile
        score, _ = StartupScore.objects.get_or_create(startup=startup)
        total = score.calculate()
        # استخدام update() بدلاً من save() لتفادي إعادة إطلاق إشارة post_save
        StartupProfile.objects.filter(pk=startup.pk).update(scorecard=total)
    except Exception:
        pass


@receiver(post_save, sender='profiles.StartupProfile')
def recalculate_score_on_profile_save(sender, instance, update_fields=None, **kwargs):
    """يُعيد حساب النقاط بعد كل تحديث لبيانات الشركة — يتجاهل التحديثات الجزئية للـ scorecard."""
    # تجنب الحلقة: إذا كان التحديث لحقل scorecard فقط نتجاهله
    if update_fields and set(update_fields) <= {'scorecard'}:
        return
    _refresh_score(instance)


@receiver(post_save, sender='profiles.StartupDocument')
def recalculate_score_on_doc_upload(sender, instance, **kwargs):
    """يُعيد حساب النقاط عند رفع وثيقة KYC جديدة."""
    _refresh_score(instance.startup)
