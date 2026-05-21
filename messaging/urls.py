from django.urls import path
from . import views

app_name = 'messaging'

urlpatterns = [
    # قائمة كل المحادثات
    path('',                                      views.index,                          name='index'),

    # محادثة الإغلاق (شركة ↔ مستثمر)
    path('open/<int:request_id>/',                views.start_or_open,                  name='open'),
    path('chat/<int:conversation_id>/',           views.chat,                           name='chat'),
    path('close/<int:conversation_id>/',          views.close_conversation,             name='close_conversation'),

    # Pitch Sessions
    path('pitch/',                                views.pitch_sessions,                 name='pitch_list'),
    path('pitch/request/<int:startup_id>/',       views.request_pitch,                  name='pitch_request'),
    path('pitch/<int:session_id>/confirm/',       views.confirm_pitch,                  name='pitch_confirm'),
    path('pitch/<int:session_id>/cancel/',        views.cancel_pitch,                   name='pitch_cancel'),

    # مستثمر ↔ مستشار
    path('advisor/<int:advisor_id>/',             views.advisor_chat,                   name='advisor_chat'),
    path('advisor/conversations/',                views.advisor_conversations,          name='advisor_conversations'),

    # شركة ناشئة ↔ مستشار
    path('startup-advisor/<int:advisor_id>/',     views.startup_advisor_chat,           name='startup_advisor_chat'),
    path('startup-advisor/conversations/',        views.startup_advisor_conversations,  name='startup_advisor_conversations'),
    path('advisor-convo/<int:convo_id>/',         views.advisor_open_chat,              name='advisor_open_chat'),
    path('startup-advisor/<int:convo_id>/close/', views.close_startup_advisor_conversation, name='close_startup_advisor'),
]