"""
RABIT — Accounts Forms
نماذج التسجيل وتسجيل الدخول
"""
from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

User = get_user_model()


class LoginForm(AuthenticationForm):
    username = forms.CharField(
        label='البريد الإلكتروني أو اسم المستخدم',
        widget=forms.TextInput(attrs={'class': 'fi', 'placeholder': 'أدخل بريدك الإلكتروني', 'dir': 'ltr'})
    )
    password = forms.CharField(
        label='كلمة المرور',
        widget=forms.PasswordInput(attrs={'class': 'fi', 'placeholder': '••••••••', 'dir': 'ltr'})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.error_messages['invalid_login'] = 'بيانات الدخول غير صحيحة.'


class RegisterForm(forms.ModelForm):

    first_name = forms.CharField(max_length=50, required=True,
        widget=forms.TextInput(attrs={'class': 'fi'}))
    last_name = forms.CharField(max_length=50, required=False,
        widget=forms.TextInput(attrs={'class': 'fi'}))
    email = forms.EmailField(required=True,
        widget=forms.EmailInput(attrs={'class': 'fi', 'dir': 'ltr'}))
    phone = forms.CharField(max_length=20, required=False,
        widget=forms.TextInput(attrs={'class': 'fi', 'dir': 'ltr'}))
    role = forms.ChoiceField(
        choices=[('startup', 'شركة ناشئة'), ('investor', 'مستثمر'), ('advisor', 'مستشار')],
        widget=forms.HiddenInput(), initial='startup',
    )
    password1 = forms.CharField(required=True,
        widget=forms.PasswordInput(attrs={'class': 'fi', 'dir': 'ltr'}))
    password2 = forms.CharField(required=True,
        widget=forms.PasswordInput(attrs={'class': 'fi', 'dir': 'ltr'}))
    agree_terms = forms.BooleanField(required=True,
        error_messages={'required': 'يجب الموافقة على الشروط والأحكام.'})

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'phone', 'role']

    def clean_email(self):
        email = self.cleaned_data.get('email', '').lower().strip()
        if User.objects.filter(email=email).exists():
            raise ValidationError('هذا البريد الإلكتروني مسجل مسبقاً.')
        return email

    def clean(self):
        cd = super().clean()
        p1 = cd.get('password1', '')
        p2 = cd.get('password2', '')
        if p1 and p2 and p1 != p2:
            self.add_error('password2', 'كلمتا المرور غير متطابقتين.')
        if p1 and len(p1) < 8:
            self.add_error('password1', 'كلمة المرور يجب أن تكون 8 أحرف على الأقل.')
        return cd

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password1'])
        user.username = self.cleaned_data['email'].lower()
        user.email    = self.cleaned_data['email'].lower()
        user.role     = self.cleaned_data['role']
        user.phone    = self.cleaned_data.get('phone', '')
        if commit:
            user.save()
            self._create_profile(user)
        return user

    def _create_profile(self, user):
        """إنشاء الـ Profile الصحيح حسب الدور."""
        from profiles.models import StartupProfile, InvestorProfile, AdvisorProfile
        if user.role == 'startup':
            StartupProfile.objects.get_or_create(user=user)
        elif user.role == 'investor':
            InvestorProfile.objects.get_or_create(user=user)
        elif user.role == 'advisor':
            AdvisorProfile.objects.get_or_create(user=user)
