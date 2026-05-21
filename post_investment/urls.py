from django.urls import path
from . import views

app_name = 'post_investment'

urlpatterns = [
    path('',                       views.index,             name='index'),
    path('ir/',                    views.ir_dashboard,      name='ir_dashboard'),
    path('report/new/',            views.report_create,     name='report_create'),
    path('report/<int:pk>/',       views.report_detail,     name='report_detail'),
    path('meeting/new/',           views.meeting_create,    name='meeting_create'),
    path('kpi/new/',               views.kpi_add,           name='kpi_add'),
    path('investor-reports/',      views.investor_reports,  name='investor_reports'),
]
