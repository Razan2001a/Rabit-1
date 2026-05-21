"""
RABIT — Core Services
دوال مساعدة عامة يستخدمها كل المشروع.
"""


def dashboard_url_for(user) -> str:
    """رجّع لينك الداش بورد الصحيح حسب الدور."""
    if user.is_staff or user.is_superuser:
        return '/control/'
    mapping = {
        'startup':  '/dashboard/startup/',
        'investor': '/dashboard/investor/',
        'advisor':  '/dashboard/advisor/',
    }
    return mapping.get(getattr(user, 'role', None), '/')


def onboarding_url_for(user) -> str:
    """رجّع لينك صفحة التهيئة (Onboarding) حسب الدور."""
    mapping = {
        'startup':  '/profiles/startup/onboarding/',
        'investor': '/profiles/investor/onboarding/',
        'advisor':  '/profiles/advisor/onboarding/',
    }
    return mapping.get(getattr(user, 'role', None), '/')
