"""
RABIT — Post-Investment Views
تقارير دورية + اجتماعات مجلس إدارة + Investor Relations dashboard
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponseForbidden

from accounts.permissions import require_startup
from profiles.models import StartupProfile
from .models import PeriodicReport, BoardMeeting, KPISnapshot


def _notify(user, title, body='', kind='info', link=''):
    try:
        from notifications.models import Notification
        Notification.notify(user=user, title=title, body=body, kind=kind, link=link)
    except Exception:
        pass


@login_required
def index(request):
    """توجيه عام."""
    if request.user.role == 'startup':
        return redirect('post_investment:ir_dashboard')
    elif request.user.role == 'investor':
        return redirect('post_investment:investor_reports')
    return redirect('core:index')


# ─────────────────────────────────────────
# STARTUP — Investor Relations
# ─────────────────────────────────────────
@require_startup
def ir_dashboard(request):
    """لوحة Investor Relations للشركة الناشئة."""
    profile, _ = StartupProfile.objects.get_or_create(user=request.user)
    reports = PeriodicReport.objects.filter(startup=profile)
    meetings = BoardMeeting.objects.filter(startup=profile)
    kpis = KPISnapshot.objects.filter(startup=profile)[:6]

    # عدد المستثمرين الحاليين
    investors_count = 0
    total_raised = 0
    try:
        from deals.models import Deal, CapTable
        closed = Deal.objects.filter(
            investor_request__startup=profile,
            status='closed'
        )
        investors_count = closed.values('investor_request__investor').distinct().count()
        total_raised = sum(float(d.final_amount or 0) for d in closed)
    except Exception:
        pass

    return render(request, 'post_investment/ir_dashboard.html', {
        'profile': profile,
        'reports': reports,
        'meetings': meetings,
        'kpis': kpis,
        'investors_count': investors_count,
        'total_raised': total_raised,
    })


@require_startup
def report_create(request):
    """إنشاء تقرير دوري جديد."""
    profile, _ = StartupProfile.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        report = PeriodicReport.objects.create(
            startup=profile,
            title=request.POST.get('title', 'تقرير دوري'),
            period=request.POST.get('period', 'quarterly'),
            summary=request.POST.get('summary', ''),
            revenue=request.POST.get('revenue') or None,
            burn_rate=request.POST.get('burn_rate') or None,
            runway_months=int(request.POST.get('runway_months', 0)),
            customers_count=int(request.POST.get('customers_count', 0)),
            team_size=int(request.POST.get('team_size', 0)),
            achievements=request.POST.get('achievements', ''),
            challenges=request.POST.get('challenges', ''),
            file=request.FILES.get('file'),
        )

        # إشعار جميع المستثمرين
        try:
            from deals.models import Deal
            investors = Deal.objects.filter(
                investor_request__startup=profile,
                status='closed'
            ).values_list('investor_request__investor', flat=True).distinct()
            from accounts.models import User
            for inv_id in investors:
                inv = User.objects.filter(pk=inv_id).first()
                if inv:
                    _notify(
                        user=inv,
                        title=f'تقرير دوري جديد — {profile.company_name}',
                        body=report.title,
                        kind='deal',
                        link=f'/post-investment/report/{report.pk}/',
                    )
        except Exception:
            pass

        messages.success(request, '✓ تم نشر التقرير وإشعار المستثمرين.')
        return redirect('post_investment:ir_dashboard')

    return render(request, 'post_investment/report_create.html', {'profile': profile})


@login_required
def report_detail(request, pk):
    """عرض تقرير دوري."""
    report = get_object_or_404(PeriodicReport, pk=pk)
    # تأكد من الصلاحيات: صاحب الشركة أو مستثمر فيها
    if request.user != report.startup.user:
        try:
            from deals.models import Deal
            allowed = Deal.objects.filter(
                investor_request__startup=report.startup,
                investor_request__investor=request.user,
                status='closed',
            ).exists()
            if not allowed and not request.user.is_superuser:
                return HttpResponseForbidden('غير مسموح')
        except Exception:
            return HttpResponseForbidden('غير مسموح')
    return render(request, 'post_investment/report_detail.html', {'report': report})


@require_startup
def meeting_create(request):
    """إنشاء اجتماع مجلس إدارة."""
    profile, _ = StartupProfile.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        BoardMeeting.objects.create(
            startup=profile,
            title=request.POST.get('title', 'اجتماع مجلس إدارة'),
            scheduled_at=request.POST.get('scheduled_at'),
            location=request.POST.get('location', ''),
            agenda=request.POST.get('agenda', ''),
        )
        messages.success(request, '✓ تم جدولة الاجتماع')
        return redirect('post_investment:ir_dashboard')
    return render(request, 'post_investment/meeting_create.html', {'profile': profile})


@require_startup
def kpi_add(request):
    """إضافة snapshot جديد لـ KPIs."""
    profile, _ = StartupProfile.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        KPISnapshot.objects.create(
            startup=profile,
            mrr=request.POST.get('mrr') or None,
            arr=request.POST.get('arr') or None,
            cac=request.POST.get('cac') or None,
            ltv=request.POST.get('ltv') or None,
            churn_pct=request.POST.get('churn_pct') or None,
            notes=request.POST.get('notes', ''),
        )
        messages.success(request, '✓ تم تسجيل KPIs')
        return redirect('post_investment:ir_dashboard')
    return render(request, 'post_investment/kpi_add.html', {'profile': profile})


# ─────────────────────────────────────────
# INVESTOR — Reports من شركات المحفظة
# ─────────────────────────────────────────
@login_required
def investor_reports(request):
    """تقارير من الشركات اللي استثمر فيها المستثمر."""
    if request.user.role != 'investor':
        return HttpResponseForbidden('غير مسموح')

    try:
        from deals.models import Deal
        portfolio_startups = Deal.objects.filter(
            investor_request__investor=request.user,
            status='closed',
        ).values_list('investor_request__startup', flat=True).distinct()
    except Exception:
        portfolio_startups = []

    reports = PeriodicReport.objects.filter(
        startup__in=portfolio_startups
    ).select_related('startup')

    return render(request, 'post_investment/investor_reports.html', {'reports': reports})
