"""
RABIT — Messaging Utils
كشف البيانات الحساسة وحجبها تلقائياً في الشات
"""
import re

# ─── أنماط البيانات الحساسة ───────────────────────────────────────
_PATTERNS = [
    # أرقام الجوال السعودية
    (r'\b(05\d[\s\-]?\d{4}[\s\-]?\d{3})\b',                    'رقم جوال'),
    (r'\b(\+9665\d{8})\b',                                       'رقم جوال دولي'),
    (r'\b(009665\d{8})\b',                                       'رقم جوال دولي'),
    # IBAN سعودي
    (r'\bSA\d{2}\s?\d{4}\s?\d{4}\s?\d{4}\s?\d{4}\s?\d{4}\b',   'رقم IBAN'),
    # أرقام الهوية الوطنية / الإقامة (10 أرقام تبدأ بـ 1 أو 2)
    (r'\b([12]\d{9})\b',                                         'رقم هوية'),
    # أرقام بطاقات الائتمان
    (r'\b(?:\d{4}[\s\-]?){4}\b',                                 'بيانات بطاقة'),
    # البريد الإلكتروني
    (r'\b[\w.\-+]+@[\w\-]+\.[a-z]{2,}\b',                        'بريد إلكتروني'),
    # روابط تواصل مباشر
    (r'(wa\.me|t\.me|telegram\.me|whatsapp)\S*',                  'رابط تواصل مباشر'),
    # عناوين IP
    (r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b',                 'عنوان شبكة'),
]

_COMPILED = [(re.compile(p, re.IGNORECASE), label) for p, label in _PATTERNS]


def detect_sensitive(text: str) -> list:
    """
    يُعيد قائمة بأنواع البيانات الحساسة الموجودة في النص.
    مثال: ['رقم جوال', 'بريد إلكتروني']
    """
    found = []
    for pattern, label in _COMPILED:
        if pattern.search(text):
            if label not in found:
                found.append(label)
    return found


def redact_sensitive(text: str) -> str:
    """يستبدل البيانات الحساسة بـ *** في النص."""
    result = text
    for pattern, label in _COMPILED:
        result = pattern.sub(f'[*** {label} محجوب ***]', result)
    return result


def is_clean(text: str) -> bool:
    """True إذا لم يكن النص يحتوي على بيانات حساسة."""
    return len(detect_sensitive(text)) == 0