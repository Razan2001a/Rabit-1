from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.db.models import Sum, Q

from .decorators import admin_required


def _base_context(request, active_page='dashboard'):
    ctx = {
        'active_page':   active_page,
        'pending_kyc':   0,
        'pending_start': 0,
        'pending_dl':    0,
        'total_users':   0,
        'total_revenue': 0,
    }
    try:
        from accounts.models import User
        ctx['total_users'] = User.objects.count()
    except: pass
    try:
        from profiles.models import InvestorProfile
        ctx['pending_kyc'] = InvestorProfile.objects.filter(kyc_submitted=True, kyc_verified=False).count()
    except: pass
    try:
        from profiles.models import StartupProfile
        ctx['pending_start'] = StartupProfile.objects.filter(status='review').count()
    except: pass
    try:
        from data_room.models import DownloadRequest
        ctx['pending_dl'] = DownloadRequest.objects.filter(status='pending').count()
    except: pass
    try:
        from payments.models import Payment
        ctx['total_revenue'] = Payment.objects.filter(status='paid').aggregate(t=Sum('amount'))['t'] or 0
    except: pass
    return ctx


@admin_required
def dashboard(request):
    ctx = _base_context(request, 'dashboard')
    try:
        from profiles.models import StartupProfile
        ctx['total_startups']  = StartupProfile.objects.count()
        ctx['listed_startups'] = StartupProfile.objects.filter(status='listed').count()
        ctx['startup_status_counts'] = {
            'مدرجة':         StartupProfile.objects.filter(status='listed').count(),
            'معتمدة':        StartupProfile.objects.filter(status='approved').count(),
            'قيد المراجعة': StartupProfile.objects.filter(status='review').count(),
            'مسودة':         StartupProfile.objects.filter(status='draft').count(),
            'مرفوضة':        StartupProfile.objects.filter(status='rejected').count(),
        }
        ctx['recent_startups'] = StartupProfile.objects.filter(
            status='review').select_related('user').order_by('-created_at')[:5]
    except:
        ctx['total_startups']        = 0
        ctx['listed_startups']       = 0
        ctx['startup_status_counts'] = {}
        ctx['recent_startups']       = []
    try:
        from deals.models import Deal
        ctx['active_deals'] = Deal.objects.filter(status__in=['negotiation','agreed']).count()
    except:
        ctx['active_deals'] = 0
    try:
        from notifications.models import Notification
        ctx['recent_activity'] = Notification.objects.select_related('user').order_by('-created_at')[:10]
    except:
        ctx['recent_activity'] = []
    return render(request, 'control_center/dashboard.html', ctx)


@admin_required
def users_list(request):
    ctx    = _base_context(request, 'users')
    try:
        from accounts.models import User
        qs     = User.objects.all().order_by('-date_joined')
        role   = request.GET.get('role', '')
        search = request.GET.get('q', '')
        status = request.GET.get('status', '')
        if role:
            qs = qs.filter(role=role)
        if status == 'verified':
            qs = qs.filter(is_verified=True)
        elif status == 'unverified':
            qs = qs.filter(is_verified=False)
        if search:
            qs = qs.filter(Q(username__icontains=search) | Q(email__icontains=search) |
                           Q(first_name__icontains=search) | Q(last_name__icontains=search))
        ctx['users']         = qs
        ctx['role_filter']   = role
        ctx['search_query']  = search
        ctx['status_filter'] = status
    except Exception as e:
        ctx['users']  = []
        ctx['error']  = str(e)
    return render(request, 'control_center/users_list.html', ctx)


@admin_required
def user_toggle_verify(request, pk):
    try:
        from accounts.models import User
        user = get_object_or_404(User, pk=pk)
        user.is_verified = not user.is_verified
        user.save(update_fields=['is_verified'])
        messages.success(request, f'تم تحديث توثيق المستخدم {user.username}.')
    except Exception as e:
        messages.error(request, str(e))
    return redirect('control_center:users_list')


@admin_required
def user_delete(request, pk):
    try:
        from accounts.models import User
        user = get_object_or_404(User, pk=pk)
        if request.method == 'POST':
            username = user.username
            user.delete()
            messages.success(request, f'تم حذف المستخدم {username}.')
    except Exception as e:
        messages.error(request, str(e))
    return redirect('control_center:users_list')


@admin_required
def startups_list(request):
    ctx = _base_context(request, 'startups')
    try:
        from profiles.models import StartupProfile
        qs     = StartupProfile.objects.select_related('user').order_by('-created_at')
        status = request.GET.get('status', '')
        stage  = request.GET.get('stage', '')
        search = request.GET.get('q', '')
        if status: qs = qs.filter(status=status)
        if stage:  qs = qs.filter(stage=stage)
        if search: qs = qs.filter(Q(company_name__icontains=search) | Q(sector__icontains=search))
        ctx['startups']       = qs
        ctx['status_filter']  = status
        ctx['stage_filter']   = stage
        ctx['search_query']   = search
        ctx['status_choices'] = StartupProfile.Status.choices
        ctx['stage_choices']  = StartupProfile.Stage.choices
    except Exception as e:
        ctx['startups']       = []
        ctx['status_choices'] = []
        ctx['stage_choices']  = []
        ctx['error']          = str(e)
    return render(request, 'control_center/startups_list.html', ctx)


@admin_required
def startup_detail(request, pk):
    ctx = _base_context(request, 'startups')
    try:
        from profiles.models import StartupProfile
        from scoring.models import StartupScore
        from deals.models import Deal, CapTable, CapTableEntry
        startup        = get_object_or_404(StartupProfile, pk=pk)
        score, _       = StartupScore.objects.get_or_create(startup=startup)
        cap, _         = CapTable.objects.get_or_create(startup=startup)
        ctx['startup']     = startup
        ctx['score']       = score
        ctx['cap_table']   = cap
        ctx['cap_entries'] = CapTableEntry.objects.filter(cap_table=cap)
        ctx['deals']       = Deal.objects.filter(
            investor_request__startup=startup).select_related('investor_request__investor').order_by('-created_at')
    except Exception as e:
        ctx['error'] = str(e)
    return render(request, 'control_center/startup_detail.html', ctx)


@admin_required
def startup_change_status(request, pk):
    try:
        from profiles.models import StartupProfile
        from notifications.models import Notification
        startup = get_object_or_404(StartupProfile, pk=pk)
        if request.method == 'POST':
            new_status = request.POST.get('status')
            startup.status = new_status
            startup.save(update_fields=['status'])
            if new_status == 'approved':
                from profiles.utils import finalize_startup_approval
                finalize_startup_approval(startup)
            elif new_status == 'listed':
                startup.status = 'listed'
                startup.save(update_fields=['status'])
            try:
                link = '/dashboard/startup/?page=status'
                Notification.notify(
                    user=startup.user,
                    title=f'تحديث حالة ملفك: {startup.get_status_display()}',
                    body='تم تحديث حالة ملف شركتك من قِبَل الإدارة.',
                    kind='approval' if new_status in ('approved', 'listed') else 'rejection',
                    link=link,
                )
            except Exception:
                pass
            messages.success(request, f'تم تغيير حالة {startup.company_name}.')
    except Exception as e:
        messages.error(request, str(e))
    return redirect('control_center:startup_detail', pk=pk)


@admin_required
def investors_list(request):
    ctx = _base_context(request, 'investors')
    try:
        from profiles.models import InvestorProfile
        qs       = InvestorProfile.objects.select_related('user').order_by('-created_at')
        inv_type = request.GET.get('type', '')
        kyc_st   = request.GET.get('kyc', '')
        search   = request.GET.get('q', '')
        if inv_type: qs = qs.filter(investor_type=inv_type)
        if kyc_st == 'verified':     qs = qs.filter(kyc_verified=True)
        elif kyc_st == 'pending':    qs = qs.filter(kyc_submitted=True, kyc_verified=False)
        elif kyc_st == 'incomplete': qs = qs.filter(kyc_submitted=False)
        if search: qs = qs.filter(Q(user__email__icontains=search) | Q(company_name__icontains=search))
        ctx['investors']    = qs
        ctx['type_filter']  = inv_type
        ctx['kyc_filter']   = kyc_st
        ctx['search_query'] = search
        ctx['type_choices'] = InvestorProfile.InvestorType.choices
    except Exception as e:
        ctx['investors']    = []
        ctx['type_choices'] = []
        ctx['error']        = str(e)
    return render(request, 'control_center/investors_list.html', ctx)


@admin_required
def kyc_list(request):
    ctx = _base_context(request, 'kyc')
    try:
        from profiles.models import InvestorProfile
        ctx['pending_investors']  = InvestorProfile.objects.filter(
            kyc_submitted=True, kyc_verified=False).select_related('user').order_by('-created_at')
        ctx['verified_investors'] = InvestorProfile.objects.filter(
            kyc_verified=True).select_related('user').order_by('-created_at')[:20]
    except Exception as e:
        ctx['pending_investors']  = []
        ctx['verified_investors'] = []
        ctx['error']              = str(e)
    return render(request, 'control_center/kyc_list.html', ctx)


@admin_required
def kyc_approve(request, pk):
    try:
        from profiles.models import InvestorProfile
        from notifications.models import Notification
        profile = get_object_or_404(InvestorProfile, pk=pk)
        profile.kyc_verified = True
        profile.kyc_submitted = True
        profile.save(update_fields=['kyc_verified', 'kyc_submitted'])
        try:
            Notification.notify(user=profile.user, title='✓ تم توثيق حسابك',
                body='تم اعتماد KYC.', kind='approval', link='/dashboard/investor/')
        except: pass
        messages.success(request, 'تم اعتماد KYC.')
    except Exception as e:
        messages.error(request, str(e))
    return redirect('control_center:kyc_list')


@admin_required
def kyc_reject(request, pk):
    try:
        from profiles.models import InvestorProfile
        from notifications.models import Notification
        profile = get_object_or_404(InvestorProfile, pk=pk)
        profile.kyc_verified  = False
        profile.kyc_submitted = False
        profile.save(update_fields=['kyc_verified','kyc_submitted'])
        try:
            Notification.notify(user=profile.user, title='✗ تم رفض طلب KYC',
                body='يرجى رفع المستندات الصحيحة.', kind='rejection', link='/dashboard/investor/')
        except: pass
        messages.warning(request, 'تم رفض KYC.')
    except Exception as e:
        messages.error(request, str(e))
    return redirect('control_center:kyc_list')


@admin_required
def advisors_list(request):
    ctx = _base_context(request, 'advisors')
    try:
        from profiles.models import AdvisorProfile
        qs        = AdvisorProfile.objects.select_related('user').order_by('-created_at')
        specialty = request.GET.get('specialty', '')
        avail     = request.GET.get('available', '')
        search    = request.GET.get('q', '')
        if specialty: qs = qs.filter(specialty=specialty)
        if avail == 'yes': qs = qs.filter(is_available=True)
        elif avail == 'no': qs = qs.filter(is_available=False)
        if search: qs = qs.filter(Q(user__first_name__icontains=search) | Q(user__last_name__icontains=search))
        ctx['advisors']          = qs
        ctx['specialty_filter']  = specialty
        ctx['avail_filter']      = avail
        ctx['search_query']      = search
        ctx['specialty_choices'] = AdvisorProfile.Specialty.choices
    except Exception as e:
        ctx['advisors']          = []
        ctx['specialty_choices'] = []
        ctx['error']             = str(e)
    return render(request, 'control_center/advisors_list.html', ctx)


@admin_required
def advisor_toggle_availability(request, pk):
    try:
        from profiles.models import AdvisorProfile
        advisor = get_object_or_404(AdvisorProfile, pk=pk)
        advisor.is_available = not advisor.is_available
        advisor.save(update_fields=['is_available'])
        messages.success(request, 'تم تحديث حالة المستشار.')
    except Exception as e:
        messages.error(request, str(e))
    return redirect('control_center:advisors_list')


@admin_required
def deals_list(request):
    ctx = _base_context(request, 'deals')
    try:
        from deals.models import Deal, InvestorRequest
        qs     = Deal.objects.select_related(
            'investor_request__startup','investor_request__investor').order_by('-created_at')
        status = request.GET.get('status', '')
        if status: qs = qs.filter(status=status)
        ctx['deals']               = qs
        ctx['status_filter']       = status
        ctx['status_choices']      = Deal.Status.choices
        ctx['requests_pending']    = InvestorRequest.objects.filter(
            status='pending').select_related('startup','investor').order_by('-created_at')
        ctx['total_closed_amount'] = Deal.objects.filter(status='closed').aggregate(
            t=Sum('final_amount'))['t'] or 0
        ctx['total_commission']    = sum(
            d.commission_amount for d in Deal.objects.filter(status='closed'))
    except Exception as e:
        ctx['deals']               = []
        ctx['status_choices']      = []
        ctx['requests_pending']    = []
        ctx['total_closed_amount'] = 0
        ctx['total_commission']    = 0
        ctx['error']               = str(e)
    return render(request, 'control_center/deals_list.html', ctx)


@admin_required
def deal_detail(request, pk):
    ctx = _base_context(request, 'deals')
    try:
        from deals.models import Deal
        deal = get_object_or_404(Deal, pk=pk)
        ctx['deal']        = deal
        ctx['term_sheets'] = deal.term_sheets.select_related('proposed_by').all()
        ctx['messages']    = deal.deal_messages.select_related('sender').all()
    except Exception as e:
        ctx['error'] = str(e)
    return render(request, 'control_center/deal_detail.html', ctx)


@admin_required
def scoring_list(request):
    ctx = _base_context(request, 'scoring')
    try:
        from profiles.models import StartupProfile
        ctx['startups'] = StartupProfile.objects.select_related('user').order_by('-scorecard')
    except Exception as e:
        ctx['startups'] = []
        ctx['error']    = str(e)
    return render(request, 'control_center/scoring_list.html', ctx)


@admin_required
def scoring_edit(request, pk):
    ctx = _base_context(request, 'scoring')
    try:
        from profiles.models import StartupProfile
        from scoring.models import StartupScore
        startup  = get_object_or_404(StartupProfile, pk=pk)
        score, _ = StartupScore.objects.get_or_create(startup=startup)
        if request.method == 'POST':
            score.team_strength   = int(request.POST.get('team_strength', 5))
            score.business_model  = int(request.POST.get('business_model', 5))
            score.market_size     = int(request.POST.get('market_size', 5))
            score.revenues        = int(request.POST.get('revenues', 5))
            score.legal_readiness = int(request.POST.get('legal_readiness', 5))
            score.tech_product    = int(request.POST.get('tech_product', 5))
            score.admin_notes     = request.POST.get('admin_notes', '')
            score.save()
            messages.success(request, f'تم حفظ نقاط {startup.company_name}.')
            return redirect('control_center:scoring_list')
        ctx['startup'] = startup
        ctx['score']   = score
    except Exception as e:
        ctx['error'] = str(e)
    return render(request, 'control_center/scoring_edit.html', ctx)


@admin_required
def advisory_list(request):
    ctx = _base_context(request, 'advisory')
    try:
        from advisory.models import ServiceRequest
        qs     = ServiceRequest.objects.select_related('startup__user','advisor__user').order_by('-created_at')
        status = request.GET.get('status', '')
        if status: qs = qs.filter(status=status)
        ctx['requests']       = qs
        ctx['status_filter']  = status
        ctx['status_choices'] = ServiceRequest.Status.choices
    except Exception as e:
        ctx['requests']       = []
        ctx['status_choices'] = []
        ctx['error']          = str(e)
    return render(request, 'control_center/advisory_list.html', ctx)


@admin_required
def payments_list(request):
    ctx = _base_context(request, 'payments')
    try:
        from payments.models import Payment
        qs     = Payment.objects.select_related('payer').order_by('-created_at')
        kind   = request.GET.get('kind', '')
        status = request.GET.get('status', '')
        if kind:   qs = qs.filter(kind=kind)
        if status: qs = qs.filter(status=status)
        ctx['payments']       = qs
        ctx['kind_filter']    = kind
        ctx['status_filter']  = status
        ctx['kind_choices']   = Payment.Kind.choices
        ctx['status_choices'] = Payment.Status.choices
        ctx['total_paid']    = Payment.objects.filter(status='paid').aggregate(t=Sum('amount'))['t'] or 0
        ctx['total_service'] = Payment.objects.filter(status='paid',kind='service').aggregate(t=Sum('amount'))['t'] or 0
        ctx['total_deal']    = Payment.objects.filter(status='paid',kind='deal').aggregate(t=Sum('amount'))['t'] or 0
        ctx['total_pending'] = Payment.objects.filter(status='pending').aggregate(t=Sum('amount'))['t'] or 0
    except Exception as e:
        ctx['payments']       = []
        ctx['kind_choices']   = []
        ctx['status_choices'] = []
        ctx['total_paid'] = ctx['total_service'] = ctx['total_deal'] = ctx['total_pending'] = 0
        ctx['error']          = str(e)
    return render(request, 'control_center/payments_list.html', ctx)


@admin_required
def dataroom_list(request):
    ctx = _base_context(request, 'dataroom')
    try:
        from data_room.models import DataRoomFile, AccessLog, DownloadRequest, NDASignature
        ctx['files']       = DataRoomFile.objects.select_related('startup').order_by('-uploaded_at')
        ctx['logs']        = AccessLog.objects.select_related('user','file').order_by('-timestamp')[:50]
        ctx['dl_requests'] = DownloadRequest.objects.filter(
            status='pending').select_related('file__startup','requester').order_by('-created_at')
        ctx['ndas']        = NDASignature.objects.select_related('investor','startup').order_by('-signed_at')[:30]
    except Exception as e:
        ctx['files'] = ctx['logs'] = ctx['dl_requests'] = ctx['ndas'] = []
        ctx['error'] = str(e)
    return render(request, 'control_center/dataroom_list.html', ctx)


@admin_required
def download_request_action(request, pk):
    try:
        from data_room.models import DownloadRequest
        from notifications.models import Notification
        dr     = get_object_or_404(DownloadRequest, pk=pk)
        action = request.POST.get('action')
        if action == 'approve':
            dr.status = 'approved'
            dr.save()
            try:
                Notification.notify(user=dr.requester, title='✓ تمت الموافقة على طلب التحميل',
                    body=f'يمكنك الآن تحميل: {dr.file.name}', kind='approval')
            except: pass
            messages.success(request, 'تمت الموافقة.')
        elif action == 'reject':
            dr.status = 'rejected'
            dr.save()
            messages.warning(request, 'تم الرفض.')
    except Exception as e:
        messages.error(request, str(e))
    return redirect('control_center:dataroom_list')


@admin_required
def notifications_list(request):
    ctx = _base_context(request, 'notifications')
    try:
        from notifications.models import Notification
        ctx['recent_notifications'] = Notification.objects.select_related('user').order_by('-created_at')[:50]
    except Exception as e:
        ctx['recent_notifications'] = []
        ctx['error']                = str(e)
    return render(request, 'control_center/notifications_list.html', ctx)


@admin_required
def send_notification(request):
    if request.method == 'POST':
        try:
            from notifications.models import Notification
            from accounts.models import User
            target = request.POST.get('target', 'all')
            title  = request.POST.get('title', '')
            body   = request.POST.get('body', '')
            kind   = request.POST.get('kind', 'info')
            link   = request.POST.get('link', '')
            if not title:
                messages.error(request, 'العنوان مطلوب.')
                return redirect('control_center:notifications_list')
            qs = User.objects.all()
            if target == 'startup':    qs = qs.filter(role='startup')
            elif target == 'investor': qs = qs.filter(role='investor')
            elif target == 'advisor':  qs = qs.filter(role='advisor')
            count = 0
            for user in qs:
                Notification.notify(user=user, title=title, body=body, kind=kind, link=link)
                count += 1
            messages.success(request, f'تم الإرسال إلى {count} مستخدم.')
        except Exception as e:
            messages.error(request, str(e))
    return redirect('control_center:notifications_list')


@admin_required
def post_investment(request):
    ctx = _base_context(request, 'post_investment')
    try:
        from post_investment.models import PeriodicReport, BoardMeeting, KPISnapshot
        ctx['reports']  = PeriodicReport.objects.select_related('startup').order_by('-sent_at')[:30]
        ctx['meetings'] = BoardMeeting.objects.select_related('startup').order_by('-scheduled_at')[:20]
        ctx['kpis']     = KPISnapshot.objects.select_related('startup').order_by('-snapshot_date')[:20]
    except Exception as e:
        ctx['reports'] = ctx['meetings'] = ctx['kpis'] = []
        ctx['error']   = str(e)
    return render(request, 'control_center/post_investment.html', ctx)


@admin_required
def admin_profile(request):
    ctx = _base_context(request, 'profile')
    if request.method == 'POST':
        try:
            user = request.user
            first_name = request.POST.get('first_name', '')
            last_name  = request.POST.get('last_name', '')
            if first_name:
                user.first_name = first_name
            if last_name:
                user.last_name = last_name
            if request.FILES.get('avatar'):
                user.avatar = request.FILES['avatar']
            user.save()
            messages.success(request, 'تم تحديث البروفايل.')
        except Exception as e:
            messages.error(request, str(e))
        return redirect('control_center:admin_profile')
    return render(request, 'control_center/admin_profile.html', ctx)