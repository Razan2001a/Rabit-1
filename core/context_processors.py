"""
RABIT — Core Context Processors
متغيرات عامة متاحة في جميع الـ templates.
"""
from django.conf import settings


def site_globals(request):
    """متغيرات عامة على مستوى الموقع."""
    return {
        'SITE_NAME': 'رابط RABIT',
        'SITE_TAGLINE': 'منصة الاستثمار الذكي',
        'DEBUG': settings.DEBUG,
    }
