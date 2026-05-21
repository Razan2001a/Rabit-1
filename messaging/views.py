"""RABIT — Messaging Views"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages as flash
from django.http import HttpResponseForbidden

from deals.models import InvestorRequest
from profiles.models import StartupProfile, AdvisorProfile
from .models import (
    Conversation, Message, SharedDataRoomFile,
    PitchSession,
    AdvisorConversation, AdvisorMessage,
    StartupAdvisorConversation, StartupAdvisorMessage,
)
from .utils import detect_sensitive, redact_sensitive


def _notify(user, title, body='', kind='info', link=''):
    try:
        from notifications.models import Notification
        Notification.notify(user=user, title=title, body=body, kind=kind, link=link)
    except Exception:
        pass


# ═══════════════════════════════════════════════════════════════
# محادثة إغلاق الصفقة — شركة ناشئة ↔ مستثمر
# ═══════════════════════════════════════════════════════════════

@login_required
def index(request):
    """قائمة المحادثات المغلقة (الأرشيف) — النشطة تُفتح من Data Room."""
    if request.user.role == 'investor':
        qs = Conversation.objects.filter(request__investor=request.user, is_closed=True)
    elif request.user.role == 'startup':
        qs = Conversation.objects.filter(request__startup__user=request.user, is_closed=True)
    else:
        qs = Conversation.objects.none()
    return render(request, 'messaging/index.html', {'conversations': qs})


@login_required
def start_or_open(request, request_id):
    """فتح أو إنشاء محادثة — يُسمح فقط بعد قبول الطلب."""
    inv_req = get_object_or_404(InvestorRequest, pk=request_id)
    if request.user not in (inv_req.investor, inv_req.startup.user):
        return HttpResponseForbidden('غير مسموح')
    if inv_req.status != InvestorRequest.Status.APPROVED:
        flash.error(request, 'لا يمكن فتح المحادثة قبل قبول الطلب.')
        fallback = 'deals:my_requests' if request.user == inv_req.investor else 'deals:requests_inbox'
        return redirect(fallback)
    convo, _ = Conversation.objects.get_or_create(request=inv_req)
    return redirect('messaging:chat', conversation_id=convo.pk)


@login_required
def chat(request, conversation_id):
    """
    شات إغلاق الصفقة:
    - كلا الطرفين يشوفون ملفات Data Room ويختارون ملفاً للنقاش
    - أي بيانات حساسة تُحجب تلقائياً
    - أي طرف يقدر ينهي المحادثة
    """
    convo = get_object_or_404(Conversation, pk=conversation_id)
    if request.user not in convo.participants.values():
        return HttpResponseForbidden('غير مسموح')

    if request.method == 'POST' and not convo.is_closed:
        action = request.POST.get('action', 'send_msg')

        # ── إضافة ملف للنقاش ──
        if action == 'pin_file':
            file_id = request.POST.get('dr_file_id')
            note    = request.POST.get('note', '').strip()
            if file_id:
                from data_room.models import DataRoomFile
                try:
                    dr_file = DataRoomFile.objects.get(pk=file_id, startup=convo.request.startup)
                    SharedDataRoomFile.objects.create(
                        conversation=convo,
                        shared_by=request.user,
                        dr_file=dr_file,
                        note=note,
                    )
                    other_user = (convo.participants['investor']
                                  if request.user == convo.participants['startup']
                                  else convo.participants['startup'])
                    _notify(
                        user=other_user,
                        title='تمت إضافة ملف للنقاش',
                        body=f'📎 {dr_file.name}',
                        kind='info',
                        link=f'/messaging/chat/{convo.pk}/',
                    )
                    flash.success(request, f'تمت إضافة "{dr_file.name}" للنقاش')
                except DataRoomFile.DoesNotExist:
                    flash.error(request, 'الملف غير موجود.')
            return redirect('messaging:chat', conversation_id=convo.pk)

        # ── إرسال رسالة نصية ──
        content_text = request.POST.get('content', '').strip()
        if content_text:
            sensitive = detect_sensitive(content_text)
            if sensitive:
                reasons = '، '.join(sensitive)
                Message.objects.create(
                    conversation=convo,
                    sender=request.user,
                    content=redact_sensitive(content_text),
                    is_blocked=True,
                    blocked_reason=f'تم حجب: {reasons}',
                )
                flash.warning(
                    request,
                    f'رسالتك تحتوي على بيانات حساسة ({reasons}) وتم حجبها تلقائياً.'
                )
            else:
                Message.objects.create(conversation=convo, sender=request.user, content=content_text)
        return redirect('messaging:chat', conversation_id=convo.pk)

    msgs         = convo.messages.select_related('sender').all()
    shared_files = convo.shared_files.select_related('dr_file', 'shared_by').all()

    from data_room.models import DataRoomFile
    dr_files   = DataRoomFile.objects.filter(startup=convo.request.startup)
    pinned_ids = set(shared_files.values_list('dr_file_id', flat=True))

    other = (convo.participants['startup']
             if request.user == convo.participants['investor']
             else convo.participants['investor'])

    embed = request.GET.get('embed') == '1'
    return render(request, 'messaging/chat.html', {
        'convo':          convo,
        'messages_list':  msgs,
        'shared_files':   shared_files,
        'dr_files':       dr_files,
        'pinned_ids':     pinned_ids,
        'other_party':    other,
        'embed':          embed,
        'base_template':  'embed_base.html' if embed else 'dashboard_base.html',
    })


@login_required
def close_conversation(request, conversation_id):
    """أي طرف يقدر ينهي المحادثة — بعدها يُعاد لقائمة المحادثات."""
    convo = get_object_or_404(Conversation, pk=conversation_id)
    if request.user not in convo.participants.values():
        return HttpResponseForbidden('غير مسموح')
    convo.is_closed = True
    convo.save(update_fields=['is_closed'])
    other = (convo.participants['investor']
             if request.user == convo.participants['startup']
             else convo.participants['startup'])
    _notify(
        user=other,
        title='تم إنهاء المحادثة',
        body=f'{request.user.get_full_name() or request.user.username} أنهى المحادثة.',
        kind='info',
        link='/messaging/',
    )
    flash.success(request, 'تم إنهاء المحادثة بنجاح.')
    return redirect('messaging:index')


# ═══════════════════════════════════════════════════════════════
# PITCH SESSIONS
# ═══════════════════════════════════════════════════════════════

@login_required
def pitch_sessions(request):
    if request.user.role == 'investor':
        qs = PitchSession.objects.filter(investor=request.user)
    elif request.user.role == 'startup':
        qs = PitchSession.objects.filter(startup__user=request.user)
    else:
        qs = PitchSession.objects.none()
    return render(request, 'messaging/pitch_list.html', {'sessions': qs.select_related('startup', 'investor')})


@login_required
def request_pitch(request, startup_id):
    if request.user.role != 'investor':
        return HttpResponseForbidden('فقط المستثمر يطلب Pitch.')
    startup = get_object_or_404(StartupProfile, pk=startup_id)
    if request.method == 'POST':
        PitchSession.objects.create(
            startup=startup,
            investor=request.user,
            agenda=request.POST.get('agenda', '').strip(),
            scheduled_at=request.POST.get('scheduled_at') or None,
            duration_min=int(request.POST.get('duration_min', 30)),
        )
        _notify(startup.user, 'طلب جلسة Pitch جديد',
                f'{request.user.get_full_name() or request.user.username} يطلب جلسة Pitch.',
                'deal', '/messaging/pitch/')
        flash.success(request, '✓ تم إرسال طلب الجلسة.')
        return redirect('messaging:pitch_list')
    return render(request, 'messaging/pitch_request.html', {'startup': startup})


@login_required
def confirm_pitch(request, session_id):
    session = get_object_or_404(PitchSession, pk=session_id)
    if request.user != session.startup.user:
        return HttpResponseForbidden('غير مسموح')
    if request.method == 'POST':
        session.scheduled_at = request.POST.get('scheduled_at') or session.scheduled_at
        session.meeting_link = request.POST.get('meeting_link', session.meeting_link)
        session.status = PitchSession.Status.SCHEDULED
        session.save()
        _notify(session.investor, 'تم تأكيد جلسة Pitch',
                f'الجلسة مُجدولة في {session.scheduled_at}', 'approval', '/messaging/pitch/')
        flash.success(request, '✓ تم جدولة الجلسة.')
    return redirect('messaging:pitch_list')


@login_required
def cancel_pitch(request, session_id):
    session = get_object_or_404(PitchSession, pk=session_id)
    if request.user not in (session.investor, session.startup.user):
        return HttpResponseForbidden('غير مسموح')
    session.status = PitchSession.Status.CANCELLED
    session.save(update_fields=['status'])
    flash.info(request, 'تم إلغاء الجلسة.')
    return redirect('messaging:pitch_list')


# ═══════════════════════════════════════════════════════════════
# مستثمر ↔ مستشار
# ═══════════════════════════════════════════════════════════════

SERVICE_NAMES  = {
    'opportunity': 'تقرير تحليل الفرصة',
    'financial':   'فحص مالي سريع',
    'full_dd':     'باقة التدقيق الكاملة',
}
SERVICE_PRICES = {
    'opportunity': 799,
    'financial':   1299,
    'full_dd':     2999,
}


@login_required
def advisor_chat(request, advisor_id):
    """محادثة مستثمر ↔ مستشار — مع كشف وحجب البيانات الحساسة."""
    advisor      = get_object_or_404(AdvisorProfile, pk=advisor_id)
    service_type = request.GET.get('service_type', '')
    service_name = SERVICE_NAMES.get(service_type, 'خدمة استشارية')
    amount       = SERVICE_PRICES.get(service_type, 0)

    convo, _ = AdvisorConversation.objects.get_or_create(
        investor=request.user,
        advisor=advisor,
        service_type=service_type,
        defaults={'service_name': service_name, 'amount': amount},
    )

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'pay' and convo.payment_status == AdvisorConversation.PaymentStatus.UNPAID:
            from payments.models import Payment
            from decimal import Decimal
            from django.utils import timezone as _tz
            _amt = Decimal(str(amount))
            Payment.objects.create(
                payer=request.user,
                payment_type=Payment.Type.ADVISOR_SERVICE,
                description=f'{service_name} — {advisor.user.get_full_name() or advisor.user.username}',
                amount=_amt,
                commission=Decimal('0'),
                vat=Decimal('0'),
                net_amount=_amt,
                status=Payment.Status.PAID,
                paid_at=_tz.now(),
                reference=f'ADVISOR-{advisor.pk}-{service_type.upper()}',
            )
            convo.payment_status = AdvisorConversation.PaymentStatus.PAID
            convo.save(update_fields=['payment_status'])
            AdvisorMessage.objects.create(
                conversation=convo,
                sender=request.user,
                content=f'✅ تم الدفع — {service_name} ({amount} ريال)',
            )
            return redirect(f'/messaging/advisor/{advisor.pk}/?service_type={convo.service_type}')

        content = request.POST.get('content', '').strip()
        if content:
            sensitive = detect_sensitive(content)
            if sensitive:
                reasons = '، '.join(sensitive)
                AdvisorMessage.objects.create(
                    conversation=convo,
                    sender=request.user,
                    content=redact_sensitive(content),
                    is_blocked=True,
                    blocked_reason=f'تم حجب: {reasons}',
                )
                flash.warning(request, f'رسالتك تحتوي على بيانات حساسة ({reasons}) وتم حجبها.')
            else:
                AdvisorMessage.objects.create(conversation=convo, sender=request.user, content=content)
        return redirect(f'/messaging/advisor/{advisor.pk}/?service_type={convo.service_type}')

    messages_list = convo.messages.select_related('sender').all()
    embed = request.GET.get('embed') == '1'
    return render(request, 'messaging/advisor_chat.html', {
        'convo':         convo,
        'advisor':       advisor,
        'messages_list': messages_list,
        'service_name':  service_name,
        'amount':        amount,
        'is_paid':       convo.payment_status == AdvisorConversation.PaymentStatus.PAID,
        'embed':         embed,
        'base_template': 'embed_base.html' if embed else 'dashboard_base.html',
    })


@login_required
def advisor_conversations(request):
    """قائمة محادثات المستشار مع المستثمرين."""
    try:
        advisor = AdvisorProfile.objects.get(user=request.user)
        convos  = AdvisorConversation.objects.filter(advisor=advisor).order_by('-created_at')
    except AdvisorProfile.DoesNotExist:
        convos = AdvisorConversation.objects.filter(investor=request.user).order_by('-created_at')
    return render(request, 'messaging/advisor_conversations.html', {'convos': convos})


# ═══════════════════════════════════════════════════════════════
# شركة ناشئة ↔ مستشار
# ═══════════════════════════════════════════════════════════════

@login_required
def startup_advisor_chat(request, advisor_id):
    """محادثة شركة ناشئة ↔ مستشار — يصل إليها كلا الطرفين."""
    advisor = get_object_or_404(AdvisorProfile, pk=advisor_id)

    # تحديد الشركة الناشئة بناءً على دور المستخدم
    if request.user.role == 'startup':
        try:
            startup = request.user.startup_profile
        except Exception:
            flash.error(request, 'يجب إكمال ملف شركتك أولاً.')
            return redirect('dashboard:startup')
    elif request.user.role == 'advisor':
        # المستشار يفتح آخر محادثة أو يُنشئ واحدة مؤقتة
        convo_qs = StartupAdvisorConversation.objects.filter(advisor=advisor).order_by('-created_at')
        if not convo_qs.exists():
            flash.error(request, 'لا توجد محادثة بعد مع أي شركة.')
            return redirect('messaging:startup_advisor_conversations')
        convo = convo_qs.first()
        startup = convo.startup
    else:
        return HttpResponseForbidden('غير مسموح')

    convo, _ = StartupAdvisorConversation.objects.get_or_create(
        startup=startup,
        advisor=advisor,
    )

    if request.method == 'POST' and not convo.is_closed:
        content = request.POST.get('content', '').strip()
        if content:
            sensitive = detect_sensitive(content)
            if sensitive:
                reasons = '، '.join(sensitive)
                StartupAdvisorMessage.objects.create(
                    conversation=convo,
                    sender=request.user,
                    content=redact_sensitive(content),
                    is_blocked=True,
                    blocked_reason=f'تم حجب: {reasons}',
                )
                flash.warning(request, f'رسالتك تحتوي على بيانات حساسة ({reasons}) وتم حجبها.')
            else:
                StartupAdvisorMessage.objects.create(
                    conversation=convo,
                    sender=request.user,
                    content=content,
                )
        return redirect('messaging:startup_advisor_chat', advisor_id=advisor.pk)

    messages_list = convo.messages.select_related('sender').all()
    embed = request.GET.get('embed') == '1'
    return render(request, 'messaging/startup_advisor_chat.html', {
        'convo':         convo,
        'advisor':       advisor,
        'startup':       startup,
        'messages_list': messages_list,
        'embed':         embed,
        'base_template': 'embed_base.html' if embed else 'dashboard_base.html',
    })


@login_required
def startup_advisor_conversations(request):
    """قائمة محادثات شركة ناشئة ↔ مستشار."""
    is_advisor = request.user.role == 'advisor'
    try:
        advisor = AdvisorProfile.objects.get(user=request.user)
        convos  = (
            StartupAdvisorConversation.objects
            .filter(advisor=advisor)
            .select_related('startup', 'startup__user', 'advisor', 'advisor__user', 'service_request')
            .order_by('-created_at')
        )
    except AdvisorProfile.DoesNotExist:
        try:
            startup = request.user.startup_profile
            convos  = (
                StartupAdvisorConversation.objects
                .filter(startup=startup)
                .select_related('startup', 'startup__user', 'advisor', 'advisor__user', 'service_request')
                .order_by('-created_at')
            )
        except Exception:
            convos = StartupAdvisorConversation.objects.none()
    profile = None
    if is_advisor:
        try:
            profile = AdvisorProfile.objects.get(user=request.user)
        except AdvisorProfile.DoesNotExist:
            pass

    return render(request, 'messaging/startup_advisor_conversations.html', {
        'convos': convos,
        'is_advisor': is_advisor,
        'profile': profile,
        'active_nav': 'conversations',
    })


@login_required
def close_startup_advisor_conversation(request, convo_id):
    """إغلاق محادثة شركة ناشئة ↔ مستشار — POST فقط."""
    convo = get_object_or_404(StartupAdvisorConversation, pk=convo_id)
    is_advisor = (request.user.role == 'advisor' and hasattr(request.user, 'advisor_profile')
                  and convo.advisor == request.user.advisor_profile)
    is_startup = (request.user.role == 'startup' and hasattr(request.user, 'startup_profile')
                  and convo.startup == request.user.startup_profile)
    if not (is_advisor or is_startup):
        return HttpResponseForbidden('غير مسموح')
    if request.method == 'POST':
        convo.is_closed = True
        convo.save(update_fields=['is_closed'])
        other = convo.advisor.user if is_startup else convo.startup.user
        _notify(other, 'تم إنهاء المحادثة',
                f'{request.user.get_full_name() or request.user.username} أنهى المحادثة.',
                'info', '/messaging/startup-advisor/conversations/')
        flash.success(request, 'تم إنهاء المحادثة بنجاح.')
    return redirect('messaging:startup_advisor_conversations')


@login_required
def advisor_open_chat(request, convo_id):
    """المستشار يفتح محادثة محددة مع شركة ناشئة."""
    convo = get_object_or_404(StartupAdvisorConversation, pk=convo_id)
    # التحقق إن المستخدم طرف في المحادثة
    is_advisor = (request.user.role == 'advisor' and hasattr(request.user, 'advisor_profile')
                  and convo.advisor == request.user.advisor_profile)
    is_startup = (request.user.role == 'startup' and hasattr(request.user, 'startup_profile')
                  and convo.startup == request.user.startup_profile)
    if not (is_advisor or is_startup):
        return HttpResponseForbidden('غير مسموح')

    if request.method == 'POST' and not convo.is_closed:
        content = request.POST.get('content', '').strip()
        if content:
            sensitive = detect_sensitive(content)
            if sensitive:
                reasons = '، '.join(sensitive)
                StartupAdvisorMessage.objects.create(
                    conversation=convo, sender=request.user,
                    content=redact_sensitive(content),
                    is_blocked=True, blocked_reason=f'تم حجب: {reasons}',
                )
                flash.warning(request, f'رسالتك تحتوي على بيانات حساسة وتم حجبها.')
            else:
                StartupAdvisorMessage.objects.create(
                    conversation=convo, sender=request.user, content=content)
        return redirect('messaging:advisor_open_chat', convo_id=convo.pk)

    messages_list = convo.messages.select_related('sender').all()
    return render(request, 'messaging/startup_advisor_chat.html', {
        'convo':         convo,
        'advisor':       convo.advisor,
        'startup':       convo.startup,
        'messages_list': messages_list,
        'base_template': 'dashboard_base.html',
    })