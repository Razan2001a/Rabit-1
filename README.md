# منصة رابط — RABIT

منصة استثمارية سعودية تربط الشركات الناشئة بالمستثمرين والمستشارين الماليين.

---

## فريق العمل

| الاسم | الدور |
|-------|-------|
| وجان العقيل | قائد الفريق — Backend & Architecture |
| شريفة الجهني | Frontend & Templates |
| أثير الحارثي | Payments & Advisory Module |
| رزان | Dashboard & Messaging |

---

## متطلبات التشغيل

| المتطلب | الإصدار |
|---------|---------|
| Python  | 3.10+   |
| pip     | 23.0+   |
| Git     | أي إصدار |

---

## تشغيل المشروع

```bash
# 1. إنشاء البيئة الافتراضية وتفعيلها
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Mac/Linux

# 2. تثبيت المكتبات
pip install -r requirements.txt

# 3. إنشاء ملف .env (انسخ من .env.example وعدّله)
copy .env.example .env

# 4. تطبيق الـ migrations
python manage.py migrate accounts
python manage.py migrate profiles
python manage.py migrate

# 5. إنشاء حساب المدير
python manage.py createsuperuser

# 6. تشغيل الخادم
python manage.py runserver
```

افتح المتصفح على: **http://127.0.0.1:8000/**

---

## ملفات المشروع

| الملف | الرابط |
|-------|--------|
| User Stories | [رابط](https://docs.google.com/document/d/LINK) |
| UML Diagrams | [رابط](https://docs.google.com/document/d/LINK) |
| Wireframe | [رابط](https://www.figma.com/file/LINK) |

---

```
