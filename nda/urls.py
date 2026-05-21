from django.urls import path
from . import views

app_name = 'nda'

urlpatterns = [
    path('', views.index, name='index'),
]
