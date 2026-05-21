"""RABIT — Scoring Views"""
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from profiles.models import StartupProfile
from .models import StartupScore


@login_required
def index(request):
    return render(request, 'scoring/index.html')


@login_required
def startup_scorecard(request, startup_id):
    startup = get_object_or_404(StartupProfile, pk=startup_id, status='listed')

    has_nda = False
    if request.user.role == 'investor':
        try:
            from data_room.models import NDASignature
            has_nda = NDASignature.objects.filter(
                investor=request.user,
                startup=startup,
                is_revoked=False
            ).exists()
        except Exception:
            has_nda = False
    elif request.user.role in ('advisor', 'admin') or request.user.is_superuser:
        has_nda = True

    score, _ = StartupScore.objects.get_or_create(startup=startup)

    similar = StartupProfile.objects.filter(
        status='listed', sector=startup.sector
    ).exclude(pk=startup.pk)
    avg_score = 0
    if similar.exists():
        avg_score = sum(s.scorecard for s in similar) // similar.count()

    def _norm(raw_val, max_val):
        """تحويل القيمة إلى مقياس 0–10 (عدد صحيح)."""
        return min(10, round((raw_val or 0) / max_val * 10))

    axes = [
        ('اكتمال البيانات',   _norm(score.score_basic    or score._calc_basic(),    15), 'ti-forms'),
        ('التوثيق والجاهزية', _norm(score.score_verified or score._calc_verified(), 20), 'ti-shield-check'),
        ('المستندات',         _norm(score.score_docs      or score._calc_docs(),     15), 'ti-files'),
        ('المالية وCap Table',_norm(score.score_financial or score._calc_financial(),15), 'ti-currency-dollar'),
        ('الفريق والمؤسسين',  _norm(score.score_team      or score._calc_team(),     10), 'ti-users'),
        ('جودة القصة',        _norm(score.score_story     or score._calc_story(),    10), 'ti-book'),
    ]

    return render(request, 'scoring/scorecard.html', {
        'startup':       startup,
        'score':         score,
        'axes':          axes,
        'avg_score':     avg_score,
        'similar_count': similar.count(),
        'has_nda':       has_nda,
    })