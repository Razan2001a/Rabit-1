from django.urls import path
from . import views

app_name = 'control_center'

urlpatterns = [
    path('',                              views.dashboard,                   name='dashboard'),
    path('users/',                        views.users_list,                  name='users_list'),
    path('users/<int:pk>/verify/',        views.user_toggle_verify,          name='user_toggle_verify'),
    path('users/<int:pk>/delete/',        views.user_delete,                 name='user_delete'),
    path('startups/',                     views.startups_list,               name='startups_list'),
    path('startups/<int:pk>/',            views.startup_detail,              name='startup_detail'),
    path('startups/<int:pk>/status/',     views.startup_change_status,       name='startup_change_status'),
    path('investors/',                    views.investors_list,               name='investors_list'),
    path('kyc/',                          views.kyc_list,                    name='kyc_list'),
    path('kyc/<int:pk>/approve/',         views.kyc_approve,                 name='kyc_approve'),
    path('kyc/<int:pk>/reject/',          views.kyc_reject,                  name='kyc_reject'),
    path('advisors/',                     views.advisors_list,               name='advisors_list'),
    path('advisors/<int:pk>/toggle/',     views.advisor_toggle_availability, name='advisor_toggle'),
    path('deals/',                        views.deals_list,                  name='deals_list'),
    path('deals/<int:pk>/',               views.deal_detail,                 name='deal_detail'),
    path('scoring/',                      views.scoring_list,                name='scoring_list'),
    path('scoring/<int:pk>/edit/',        views.scoring_edit,                name='scoring_edit'),
    path('advisory/',                     views.advisory_list,               name='advisory_list'),
    path('payments/',                     views.payments_list,               name='payments_list'),
    path('dataroom/',                     views.dataroom_list,               name='dataroom_list'),
    path('dataroom/dl/<int:pk>/action/',  views.download_request_action,     name='dl_request_action'),
    path('notifications/',                views.notifications_list,          name='notifications_list'),
    path('notifications/send/',           views.send_notification,           name='send_notification'),
    path('post-investment/',              views.post_investment,             name='post_investment'),
    path('profile/', views.admin_profile, name='admin_profile'),
]