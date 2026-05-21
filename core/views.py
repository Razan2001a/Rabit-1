"""
RABIT — Core Views
الصفحات العامة (Landing Pages)
"""
from django.shortcuts import render
from django.http import HttpRequest
from django.contrib import messages


def index(request: HttpRequest):
    return render(request, 'core/index.html')


def about(request: HttpRequest):
    return render(request, 'core/about.html')


def contact(request: HttpRequest):
    if request.method == 'POST':
        name    = request.POST.get('name', '').strip()
        email   = request.POST.get('email', '').strip()
        subject = request.POST.get('subject', '').strip()
        body    = request.POST.get('body', '').strip()
        if name and email and body:
            try:
                from django.core.mail import send_mail
                send_mail(
                    subject=f'[تواصل معنا] {subject or "رسالة جديدة"} — {name}',
                    message=f'من: {name}\nالبريد: {email}\n\n{body}',
                    from_email=None,
                    recipient_list=['rabitplatform@gmail.com'],
                )
            except Exception:
                pass
            messages.success(request, '✓ تم إرسال رسالتك بنجاح. سنتواصل معك خلال 24 ساعة.')
        else:
            messages.error(request, 'يرجى تعبئة جميع الحقول المطلوبة.')
    return render(request, 'core/contact.html')


def public_investors(request: HttpRequest):
    from profiles.models import InvestorProfile
    investors = InvestorProfile.objects.filter(
        kyc_verified=True
    ).select_related('user').order_by('-portfolio_count', '-investor_rating')

    inv_type = request.GET.get('type', '')
    search   = request.GET.get('q', '').strip()
    if inv_type:
        investors = investors.filter(investor_type=inv_type)
    if search:
        investors = (
            InvestorProfile.objects.filter(kyc_verified=True, company_name__icontains=search) |
            InvestorProfile.objects.filter(kyc_verified=True, bio__icontains=search) |
            InvestorProfile.objects.filter(kyc_verified=True, sectors_interest__icontains=search)
        ).select_related('user').distinct()

    investor_types = InvestorProfile.InvestorType.choices
    return render(request, 'core/public_investors.html', {
        'investors': investors,
        'investor_types': investor_types,
        'sel_type': inv_type,
        'search': search,
        'total': investors.count(),
    })


def public_advisors(request: HttpRequest):
    from profiles.models import AdvisorProfile
    advisors = AdvisorProfile.objects.select_related('user').order_by('-is_available', '-rating', '-services_count')

    specialty = request.GET.get('specialty', '')
    search    = request.GET.get('q', '').strip()
    available = request.GET.get('available', '')
    if specialty:
        advisors = advisors.filter(specialty=specialty)
    if available:
        advisors = advisors.filter(is_available=True)
    if search:
        advisors = (
            AdvisorProfile.objects.filter(title__icontains=search) |
            AdvisorProfile.objects.filter(bio__icontains=search)
        ).select_related('user').distinct()

    specialties = AdvisorProfile.Specialty.choices
    return render(request, 'core/public_advisors.html', {
        'advisors': advisors,
        'specialties': specialties,
        'sel_specialty': specialty,
        'sel_available': available,
        'search': search,
        'total': advisors.count(),
    })


def public_startups(request: HttpRequest):
    from profiles.models import StartupProfile
    startups = StartupProfile.objects.filter(
        status='listed'
    ).select_related('user').order_by('-scorecard', '-profile_completion')

    sector = request.GET.get('sector', '')
    stage  = request.GET.get('stage', '')
    search = request.GET.get('q', '').strip()
    if sector:
        startups = startups.filter(sector=sector)
    if stage:
        startups = startups.filter(stage=stage)
    if search:
        startups = (
            StartupProfile.objects.filter(status='listed', company_name__icontains=search) |
            StartupProfile.objects.filter(status='listed', tagline__icontains=search)
        ).select_related('user').distinct()

    sectors = StartupProfile.objects.filter(status='listed').values_list('sector', flat=True).distinct()
    stages  = StartupProfile.Stage.choices
    return render(request, 'core/public_startups.html', {
        'startups': startups,
        'sectors': sectors,
        'stages': stages,
        'sel_sector': sector,
        'sel_stage': stage,
        'search': search,
        'total': startups.count(),
    })

def privacy_policy(request):
    return render(request, 'core/privacy_policy.html')

def terms_conditions(request):
    return render(request, 'core/terms_conditions.html')

def nda_policy(request):
    return render(request, 'core/nda_policy.html')

def index(request: HttpRequest):
    """Public homepage — توجيه المستخدمين المسجلين لداشبورداتهم مباشرة."""
    if request.user.is_authenticated:
        from django.shortcuts import redirect
        if request.user.is_staff or request.user.is_superuser:
            return redirect('/control/')
        # توجيه مباشر حسب الدور — لا تُعرض صفحة الترحيب
        role_map = {
            'startup':  '/dashboard/startup/',
            'investor': '/dashboard/investor/',
            'advisor':  '/dashboard/advisor/',
        }
        dest = role_map.get(getattr(request.user, 'role', ''))
        if dest:
            return redirect(dest)

    featured = []
    try:
        from profiles.models import StartupProfile
        from data_room.models import DataRoomFile
        qs = StartupProfile.objects.filter(
            status='listed'
        ).order_by('-scorecard', '-dd_level')[:3]

        for st in qs:
            name = st.company_name or ''
            sector = st.sector or ''
            initials = (name[:2] if name else sector[:2]).upper() or 'ST'
            files = DataRoomFile.objects.filter(startup=st)
            public_files = files.filter(access='public')
            nda_files = files.filter(access='nda')
            featured.append({
                'obj': st,
                'initials': initials,
                'public_files': public_files,
                'nda_files': nda_files,
                'has_nda_files': nda_files.exists(),
                'nda_count': nda_files.count(),
                'public_count': public_files.count(),
            })
    except Exception:
        pass

    return render(request, 'core/index.html', {'featured': featured})