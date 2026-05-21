"""
RABIT — Notifications Context Processor
يضيف عدد الإشعارات غير المقروءة لكل صفحة.
"""


def unread_count(request):
    """يرجع dict يحتوي عدد الإشعارات غير المقروءة للمستخدم الحالي."""
    if not request.user.is_authenticated:
        return {'unread_notifications': 0}
    try:
        from .models import Notification
        count = Notification.objects.filter(user=request.user, is_read=False).count()
    except Exception:
        count = 0
    return {'unread_notifications': count}
