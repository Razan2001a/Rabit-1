"""
RABIT — Accounts Views
تسجيل الدخول / إنشاء حساب / التحقق من الإيميل
"""
import random
from datetime import timedelta

from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.mail import send_mail
from django.utils import timezone
from django.http import HttpRequest

from .forms import RegisterForm
from .models import EmailVerificationCode
from core.services import dashboard_url_for, onboarding_url_for


# ─────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────

def _send_code(user):
    """توليد رمز 6 أرقام وإرساله على الإيميل """
    code = str(random.randint(100000, 999999))
    expires = timezone.now() + timedelta(minutes=10)
    EmailVerificationCode.objects.update_or_create(
        user=user,
        defaults={'code': code, 'expires_at': expires}
    )
    send_mail(
        subject='رمز التحقق من حسابك — رابط RABIT',
        message=f'رمز التحقق الخاص بك هو: {code}\nصالح لمدة 10 دقائق.',
        from_email=None,
        recipient_list=[user.email],
        html_message=f"""
        <div dir="rtl" style="font-family:Arial,sans-serif;max-width:480px;margin:auto;padding:32px;background:#f7fafc;border-radius:12px">
          <div style="text-align:center;margin-bottom:24px">
            <div style="display:inline-block;background:linear-gradient(135deg,#2563EB,#7C3AED);color:#fff;font-size:1.1rem;font-weight:900;padding:10px 20px;border-radius:8px">
              رابط RABIT
            </div>
          </div>
          <h2 style="text-align:center;color:#0F172A;margin-bottom:8px">رمز التحقق من بريدك الإلكتروني</h2>
          <p style="text-align:center;color:#64748B;margin-bottom:28px">أدخل الرمز التالي في صفحة التحقق</p>
          <div style="text-align:center;background:#fff;border:2px solid #BFDBFE;border-radius:12px;padding:28px;margin-bottom:24px">
            <div style="font-size:2.8rem;font-weight:900;letter-spacing:12px;color:#2563EB">{code}</div>
            <div style="color:#94A3B8;font-size:.8rem;margin-top:8px">صالح لمدة <strong>10 دقائق</strong></div>
          </div>
          <p style="color:#94A3B8;font-size:.75rem;text-align:center">إذا لم تطلب هذا الرمز، تجاهل هذه الرسالة.</p>
        </div>
        """,
    )


# ─────────────────────────────────────────
# VIEWS
# ─────────────────────────────────────────

def login_view(request: HttpRequest):
    if request.user.is_authenticated:
        if not request.user.is_verified:
            return redirect('/accounts/verify-email/')
        return redirect(dashboard_url_for(request.user))

    form = AuthenticationForm(request, data=request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.get_user()
        login(request, user)
        if not user.is_verified:
            _send_code(user)
            return redirect('/accounts/verify-email/')
        messages.success(request, f'مرحباً بعودتك، {user.first_name or user.username}!')
        return redirect(request.GET.get('next') or dashboard_url_for(user))
    elif request.method == 'POST':
        messages.error(request, 'بيانات الدخول غير صحيحة.')

    return render(request, 'accounts/login.html', {'form': form})


def register_view(request: HttpRequest):
    if request.user.is_authenticated:
        return redirect(dashboard_url_for(request.user))

    initial_role = request.GET.get('role', 'startup')

    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            _send_code(user)
            messages.success(request, 'تم إنشاء حسابك! أرسلنا رمز التحقق على بريدك.')
            return redirect('/accounts/verify-email/')
        initial_role = request.POST.get('role', 'startup')
        return render(request, 'accounts/register.html', {
            'form': form, 'initial_role': initial_role,
        })

    form = RegisterForm(initial={'role': initial_role})
    return render(request, 'accounts/register.html', {
        'form': form, 'initial_role': initial_role,
    })


@login_required
def verify_email_view(request: HttpRequest):
    """صفحة إدخال رمز التحقق المكوّن من 6 أرقام."""
    user = request.user

    if user.is_verified:
        return redirect(dashboard_url_for(user))

    error = None

    if request.method == 'POST':
        action = request.POST.get('action')

        # ── إعادة إرسال الرمز ──
        if action == 'resend':
            _send_code(user)
            messages.success(request, 'تم إرسال رمز جديد على بريدك الإلكتروني.')
            return redirect('/accounts/verify-email/')

        # ── التحقق من الرمز ──
        digits = [request.POST.get(f'd{i}', '') for i in range(1, 7)]
        entered = ''.join(digits).strip()

        if len(entered) != 6 or not entered.isdigit():
            error = 'أدخل الرمز المكوّن من 6 أرقام كاملاً.'
        else:
            try:
                record = EmailVerificationCode.objects.get(user=user)
                if record.is_expired():
                    error = 'انتهت صلاحية الرمز. اضغط "إعادة الإرسال" للحصول على رمز جديد.'
                elif record.code != entered:
                    error = 'الرمز غير صحيح. تحقق من بريدك وأعد المحاولة.'
                else:
                    user.is_verified = True
                    user.save(update_fields=['is_verified'])
                    record.delete()
                    messages.success(request, 'تم التحقق من بريدك الإلكتروني بنجاح! 🎉')
                    return redirect(onboarding_url_for(user))
            except EmailVerificationCode.DoesNotExist:
                _send_code(user)
                error = 'لا يوجد رمز نشط. أرسلنا لك رمزاً جديداً.'

    return render(request, 'accounts/verify_email.html', {
        'email': user.email,
        'error': error,
    })


@login_required
def logout_view(request: HttpRequest):
    logout(request)
    messages.info(request, 'تم تسجيل خروجك بنجاح.')
    return redirect('core:index')


@login_required
def dashboard_redirect(request: HttpRequest):
    """توجيه المستخدم إلى لوحة التحكم الخاصة بدوره."""
    if not request.user.is_verified:
        return redirect('/accounts/verify-email/')
    return redirect(dashboard_url_for(request.user))


@login_required
def change_password_view(request: HttpRequest):
    """تغيير كلمة المرور — يتطلب كلمة المرور الحالية."""
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # عشان ما يتم تسجيل خروج تلقائي
            messages.success(request, '✓ تم تغيير كلمة المرور بنجاح!')
            return redirect('accounts:change_password')
        else:
            messages.error(request, 'يرجى تصحيح الأخطاء أدناه.')
    else:
        form = PasswordChangeForm(request.user)

    return render(request, 'accounts/change_password.html', {'form': form})
