from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'accounts'

urlpatterns = [
    path('login/',         views.login_view,          name='login'),
    path('register/',      views.register_view,       name='register'),
    path('logout/',        views.logout_view,         name='logout'),
    path('dashboard/',     views.dashboard_redirect,  name='dashboard'),
    path('verify-email/',  views.verify_email_view,   name='verify_email'),

    # Password change
    path('change-password/',  views.change_password_view,  name='change_password'),

    # Password reset (forgot password)
    path('password-reset/',
         auth_views.PasswordResetView.as_view(
             html_email_template_name='accounts/password_reset_email.html',
             template_name='accounts/password_reset.html',
             email_template_name='accounts/password_reset_email.html',
             success_url='/accounts/password-reset/done/',
         ),
         name='password_reset'),
    path('password-reset/done/',
         auth_views.PasswordResetDoneView.as_view(
             template_name='accounts/password_reset_done.html'),
         name='password_reset_done'),
    path('password-reset-confirm/<uidb64>/<token>/',
         auth_views.PasswordResetConfirmView.as_view(
             template_name='accounts/password_reset_confirm.html',
             success_url='/accounts/password-reset-complete/',
         ),
         name='password_reset_confirm'),
    path('password-reset-complete/',
         auth_views.PasswordResetCompleteView.as_view(
             template_name='accounts/password_reset_complete.html'),
         name='password_reset_complete'),
]
