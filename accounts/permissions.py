"""
RABIT — Accounts Permissions
ديكوريترز للتحقق من الأدوار.
"""
from functools import wraps
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import redirect


def require_role(role_name: str, redirect_to: str = '/'):
    """ديكوريتر يتأكد من أن المستخدم له دور معين + موثّق."""
    def decorator(view_func):
        @wraps(view_func)
        @login_required(login_url='/accounts/login/')
        def wrapper(request, *args, **kwargs):
            if not request.user.is_verified:
                return redirect('/accounts/verify-email/')
            if request.user.role != role_name:
                messages.error(request, f'هذه الصفحة مخصصة لـ {role_name} فقط.')
                return redirect(redirect_to)
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


require_startup  = require_role('startup')
require_investor = require_role('investor')
require_advisor  = require_role('advisor')
