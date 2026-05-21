"""
RABIT — Core Middleware
- KYCMiddleware: يمنع المستخدم من الوصول للوحة قبل إكمال KYC.
"""
from django.shortcuts import redirect


ALLOWED_PATHS = (
    '/accounts/login/',
    '/accounts/logout/',
    '/accounts/register/',
    '/accounts/verify-email/',
    '/accounts/password-reset/',
    '/accounts/password-reset-confirm/',
    '/accounts/password-reset-complete/',
    '/accounts/change-password/',
    '/profiles/investor/onboarding/',
    '/profiles/investor/kyc-upload/',
    '/profiles/investor/save-preferences/',
    '/profiles/investor/edit/',
    '/profiles/investor/preferences/',
    '/deals/',
    '/payments/checkout',
    '/payments/callback/',
    '/payments/confirm-investment/',
    '/profiles/startup/onboarding/',
    '/profiles/advisor/onboarding/',
    '/admin/',
    '/static/',
    '/media/',
    '/control/',
)


class KYCMiddleware:
    """إجبار المستثمر على إكمال KYC قبل الوصول لأي صفحة."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        u = request.user

        if not u.is_authenticated:
            return self.get_response(request)

        if u.is_superuser or getattr(u, 'role', None) == 'admin':
            return self.get_response(request)

        path = request.path
        for p in ALLOWED_PATHS:
            if path.startswith(p):
                return self.get_response(request)

        if not u.is_verified:
            return redirect('/accounts/verify-email/')

        # المستثمر: إكمال التسجيل فقط — بعد الإرسال يبقى «معلق» حتى اعتماد الأدمن
        if u.role == 'investor':
            try:
                from profiles.investor_kyc import get_investor_profile, investor_must_complete_onboarding
                profile = get_investor_profile(u)
                if investor_must_complete_onboarding(profile):
                    return redirect('/profiles/investor/onboarding/')
            except Exception:
                return redirect('/profiles/investor/onboarding/')

        return self.get_response(request)


class RoleRedirectMiddleware:
    """Middleware اختياري لتوجيه المستخدم حسب الدور."""
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)
