"""
Migration: استبدال حقول النقاط اليدوية بحقول النقاط التلقائية (9 معايير)
"""
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('scoring', '0002_alter_startupscore_business_model_and_more'),
    ]

    operations = [
        # إزالة الحقول اليدوية القديمة وإضافة الجديدة
        migrations.RemoveField(model_name='startupscore', name='team_strength'),
        migrations.RemoveField(model_name='startupscore', name='business_model'),
        migrations.RemoveField(model_name='startupscore', name='market_size'),
        migrations.RemoveField(model_name='startupscore', name='revenues'),
        migrations.RemoveField(model_name='startupscore', name='legal_readiness'),
        migrations.RemoveField(model_name='startupscore', name='tech_product'),
        # إضافة 9 معايير جديدة (nullable = يُحسب تلقائياً إذا كان null)
        migrations.AddField(
            model_name='startupscore', name='score_basic',
            field=models.FloatField(blank=True, null=True, help_text='اكتمال البيانات الأساسية /15'),
        ),
        migrations.AddField(
            model_name='startupscore', name='score_verified',
            field=models.FloatField(blank=True, null=True, help_text='شارة التوثيق /20'),
        ),
        migrations.AddField(
            model_name='startupscore', name='score_docs',
            field=models.FloatField(blank=True, null=True, help_text='المستندات /15'),
        ),
        migrations.AddField(
            model_name='startupscore', name='score_financial',
            field=models.FloatField(blank=True, null=True, help_text='المالية + CapTable /15'),
        ),
        migrations.AddField(
            model_name='startupscore', name='score_story',
            field=models.FloatField(blank=True, null=True, help_text='جودة القصة /10'),
        ),
        migrations.AddField(
            model_name='startupscore', name='score_team',
            field=models.FloatField(blank=True, null=True, help_text='الفريق والمؤسسين /10'),
        ),
        migrations.AddField(
            model_name='startupscore', name='score_activity',
            field=models.FloatField(blank=True, null=True, help_text='النشاط والتقارير /5'),
        ),
        migrations.AddField(
            model_name='startupscore', name='score_video',
            field=models.FloatField(blank=True, null=True, help_text='فيديو تعريفي /5'),
        ),
        migrations.AddField(
            model_name='startupscore', name='score_website',
            field=models.FloatField(blank=True, null=True, help_text='الموقع الإلكتروني /5'),
        ),
    ]
