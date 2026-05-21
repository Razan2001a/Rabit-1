from django.urls import path
from . import views

app_name = 'scoring'

urlpatterns = [
    path('', views.index, name='index'),
    path('scorecard/<int:startup_id>/', views.startup_scorecard, name='scorecard'),
]
