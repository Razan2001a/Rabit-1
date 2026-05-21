from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, EmailVerificationCode


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display  = ('username', 'email', 'first_name', 'last_name', 'role', 'is_verified', 'date_joined')
    list_filter   = ('role', 'is_verified', 'is_staff')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Rabit Fields', {'fields': ('role', 'phone', 'avatar', 'is_verified')}),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Rabit Fields', {'fields': ('role', 'phone')}),
    )


@admin.register(EmailVerificationCode)
class EmailVerificationCodeAdmin(admin.ModelAdmin):
    list_display  = ('user', 'code', 'created_at', 'expires_at')
    search_fields = ('user__email',)
    readonly_fields = ('created_at',)
