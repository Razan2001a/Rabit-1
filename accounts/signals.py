"""
RABIT — Accounts Signals
"""
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from .models import User


@receiver(pre_save, sender=User)
def superuser_becomes_admin(sender, instance, **kwargs):
    """
    أي superuser يُسجَّل (سواء عبر createsuperuser أو من الإدارة) يصبح
    تلقائياً Admin role + verified + كل الصلاحيات.
    """
    if instance.is_superuser:
        # دور الإدارة
        instance.role = User.Role.ADMIN
        # موثّق تلقائياً
        instance.is_verified = True
        # staff لازم يكون True للوصول لـ /admin/
        instance.is_staff = True


@receiver(post_save, sender=User)
def create_role_profile(sender, instance, created, **kwargs):
    """ضمان وجود Profile لكل مستخدم حسب دوره (ما عدا admin)."""
    if not created:
        return
    if instance.is_superuser or instance.role == User.Role.ADMIN:
        return  # الـ admin ما يحتاج profile

    from profiles.models import StartupProfile, InvestorProfile, AdvisorProfile
    if instance.role == User.Role.STARTUP:
        StartupProfile.objects.get_or_create(user=instance)
    elif instance.role == User.Role.INVESTOR:
        InvestorProfile.objects.get_or_create(user=instance)
    elif instance.role == User.Role.ADVISOR:
        AdvisorProfile.objects.get_or_create(user=instance)
