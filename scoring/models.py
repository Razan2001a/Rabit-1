"""
RABIT — Scoring Models
StartupScore: حساب تلقائي (9 معايير) + خيار تعديل يدوي من الأدمن
AdvisorRating: تقييم المستشارين
"""
from django.db import models
from django.utils import timezone


class AdvisorRating(models.Model):
    """تقييم لمستشار من شركة ناشئة بعد إكمال خدمة."""
    advisor    = models.ForeignKey('profiles.AdvisorProfile', on_delete=models.CASCADE, related_name='ratings')
    startup    = models.ForeignKey('profiles.StartupProfile', on_delete=models.CASCADE, related_name='given_ratings')
    service    = models.ForeignKey('advisory.ServiceRequest', on_delete=models.CASCADE, null=True, blank=True)
    score      = models.PositiveSmallIntegerField(default=5, help_text='1 إلى 5')
    review     = models.TextField(blank=True, verbose_name='تعليق')
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        verbose_name = 'تقييم مستشار'
        verbose_name_plural = 'تقييمات المستشارين'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.startup} → {self.advisor} ({self.score}/5)'

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self._update_advisor_avg()

    def _update_advisor_avg(self):
        from django.db.models import Avg
        agg = self.advisor.ratings.aggregate(avg=Avg('score'))
        # لا تضع قيمة افتراضية 5.0 — إن لم تكن هناك تقييمات تُعرض 0
        avg = agg['avg'] if agg['avg'] is not None else 0.0
        self.advisor.rating = round(float(avg), 1)
        self.advisor.save(update_fields=['rating'])


class StartupScore(models.Model):
    """
    Scorecard للشركة الناشئة — حساب تلقائي بناءً على 9 معايير.
    الأدمن يستطيع تعديل النقاط يدوياً (admin_override).
    """
    startup          = models.OneToOneField('profiles.StartupProfile', on_delete=models.CASCADE, related_name='score_detail')
    # 9 معايير (يمكن للأدمن التعديل — None = يُحسب تلقائياً)
    score_basic      = models.FloatField(null=True, blank=True, help_text='اكتمال البيانات الأساسية /15')
    score_verified   = models.FloatField(null=True, blank=True, help_text='شارة التوثيق /20')
    score_docs       = models.FloatField(null=True, blank=True, help_text='المستندات /15')
    score_financial  = models.FloatField(null=True, blank=True, help_text='المالية + CapTable /15')
    score_story      = models.FloatField(null=True, blank=True, help_text='جودة القصة /10')
    score_team       = models.FloatField(null=True, blank=True, help_text='الفريق والمؤسسين /10')
    score_activity   = models.FloatField(null=True, blank=True, help_text='النشاط والتقارير /5')
    score_video      = models.FloatField(null=True, blank=True, help_text='فيديو تعريفي /5')
    score_website    = models.FloatField(null=True, blank=True, help_text='الموقع الإلكتروني /5')
    admin_notes      = models.TextField(blank=True, verbose_name='ملاحظات الإدارة')
    updated_at       = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'نقاط شركة'
        verbose_name_plural = 'نقاط الشركات'

    def __str__(self):
        return f'{self.startup} — {self.calculate()}/100'

    def calculate(self) -> int:
        """الحساب التلقائي للـ StartupScore حسب 9 معايير."""
        startup = self.startup
        score = 0.0

        # 1. البيانات الأساسية (15%)
        s = self.score_basic
        if s is None:
            basic_fields = [
                startup.company_name, startup.sector, startup.stage,
                startup.founded_year, startup.team_size, startup.city,
                startup.tagline or startup.problem_desc,
            ]
            filled = sum(1 for f in basic_fields if f)
            s = (filled / len(basic_fields)) * 15
        score += s

        # 2. التوثيق (20%) — الشركة دفعت 799 ريال + اكتملت الخدمات
        s = self.score_verified
        if s is None:
            try:
                act = startup.activation
                s = 20.0 if act.status == 'completed' else 0.0
            except Exception:
                s = 20.0 if startup.status == 'listed' else 0.0
        score += s

        # 3. المستندات (15%)
        s = self.score_docs
        if s is None:
            try:
                from profiles.models import StartupDocument
                doc_types = ['commercial_register', 'founding_contract', 'national_id']
                uploaded = StartupDocument.objects.filter(startup=startup, doc_type__in=doc_types).values_list('doc_type', flat=True)
                has = len(set(uploaded))
                s = (has / len(doc_types)) * 15
            except Exception:
                s = 0.0
        score += s

        # 4. المالية + CapTable (15%)
        s = self.score_financial
        if s is None:
            s = 0.0
            if startup.funding_target and startup.equity_offered and startup.valuation:
                s += 5.0
            try:
                cap = startup.cap_table
                if cap:
                    s += 10.0
            except Exception:
                pass
        score += s

        # 5. جودة القصة (10%)
        s = self.score_story
        if s is None:
            s = 0.0
            if startup.problem_desc and len(startup.problem_desc) > 200:
                s += 5.0
            if startup.tagline and startup.use_of_funds:
                s += 5.0
        score += s

        # 6. الفريق والمؤسسين (10%)
        s = self.score_team
        if s is None:
            s = 0.0
            if startup.founder_bio:
                s += 5.0
            if startup.team_size and startup.team_size >= 2:
                s += 5.0
        score += s

        # 7. النشاط — تقارير حديثة خلال 90 يوم (5%)
        s = self.score_activity
        if s is None:
            s = 0.0
            try:
                from django.utils import timezone as tz
                last_report = startup.ir_reports.order_by('-sent_at').first()
                if last_report:
                    days_ago = (tz.now() - last_report.sent_at).days
                    if days_ago <= 90:
                        s = 5.0
            except Exception:
                pass
        score += s

        # 8. فيديو تعريفي (5%)
        s = self.score_video
        if s is None:
            s = 5.0 if startup.video_url else 0.0
        score += s

        # 9. الموقع الإلكتروني (5%)
        s = self.score_website
        if s is None:
            s = 5.0 if startup.website else 0.0
        score += s

        return round(score)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # تحديث الـ scorecard في الـ StartupProfile
        total = self.calculate()
        self.startup.scorecard = total
        self.startup.save(update_fields=['scorecard'])

    def get_breakdown(self):
        """إرجاع التفاصيل لعرضها في الواجهة."""
        startup = self.startup
        breakdown = []

        def _row(label, actual, max_pts, tip=None):
            breakdown.append({
                'label': label, 'score': round(actual, 1), 'max': max_pts,
                'pct': round((actual / max_pts * 100) if max_pts else 0),
                'tip': tip,
            })

        # نستعيد كل قيمة بنفس منطق calculate
        _row('البيانات الأساسية', self.score_basic or self._calc_basic(), 15,
             'أكمل اسم الشركة، القطاع، المرحلة، المدينة، وصف الشركة')
        _row('التوثيق (799 ريال)', self.score_verified or self._calc_verified(), 20,
             'ادفع رسوم التفعيل لتحصل على الشارة الموثّقة')
        _row('المستندات المرفوعة', self.score_docs or self._calc_docs(), 15,
             'ارفع السجل التجاري وعقد التأسيس والهوية الوطنية')
        _row('المالية + Cap Table', self.score_financial or self._calc_financial(), 15,
             'أضف التقييم والحصة المعروضة وجدول الملكية')
        _row('جودة القصة', self.score_story or self._calc_story(), 10,
             'اكتب وصف المشكلة والحل بإسهاب (200+ حرف)')
        _row('الفريق والمؤسسين', self.score_team or self._calc_team(), 10,
             'أضف نبذة المؤسس وفريق العمل')
        _row('النشاط (تقارير حديثة)', self.score_activity or self._calc_activity(), 5,
             'ارفع تقريراً دورياً كل 3 أشهر على الأقل')
        _row('فيديو تعريفي', self.score_video or (5.0 if startup.video_url else 0.0), 5,
             'أضف رابط فيديو تعريفي لشركتك')
        _row('الموقع الإلكتروني', self.score_website or (5.0 if startup.website else 0.0), 5,
             'أضف موقعك الإلكتروني')
        return breakdown

    # helpers لحساب كل معيار بشكل منفصل
    def _calc_basic(self):
        s = self.startup
        fields = [s.company_name, s.sector, s.stage, s.founded_year, s.team_size, s.city, s.tagline or s.problem_desc]
        return (sum(1 for f in fields if f) / len(fields)) * 15

    def _calc_verified(self):
        try:
            return 20.0 if self.startup.activation.status == 'completed' else 0.0
        except Exception:
            return 20.0 if self.startup.status == 'listed' else 0.0

    def _calc_docs(self):
        try:
            from profiles.models import StartupDocument
            types = ['commercial_register', 'founding_contract', 'national_id']
            has = len(set(StartupDocument.objects.filter(startup=self.startup, doc_type__in=types).values_list('doc_type', flat=True)))
            return (has / len(types)) * 15
        except Exception:
            return 0.0

    def _calc_financial(self):
        s = self.startup
        pts = 0.0
        if s.funding_target and s.equity_offered and s.valuation:
            pts += 5.0
        try:
            if s.cap_table:
                pts += 10.0
        except Exception:
            pass
        return pts

    def _calc_story(self):
        s = self.startup
        pts = 0.0
        if s.problem_desc and len(s.problem_desc) > 200:
            pts += 5.0
        if s.tagline and s.use_of_funds:
            pts += 5.0
        return pts

    def _calc_team(self):
        s = self.startup
        pts = 0.0
        if s.founder_bio:
            pts += 5.0
        if s.team_size and s.team_size >= 2:
            pts += 5.0
        return pts

    def _calc_activity(self):
        try:
            from django.utils import timezone as tz
            last = self.startup.ir_reports.order_by('-sent_at').first()
            if last and (tz.now() - last.sent_at).days <= 90:
                return 5.0
        except Exception:
            pass
        return 0.0
