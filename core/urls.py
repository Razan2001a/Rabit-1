from django.urls import path
from . import views

app_name = "core"

urlpatterns = [
    path('',            views.index,            name='index'),
    path('about/',      views.about,            name='about'),
    path('contact/',    views.contact,          name='contact'),
    path('investors/',  views.public_investors, name='public_investors'),
    path('advisors/',   views.public_advisors,  name='public_advisors'),
    path('startups/',   views.public_startups,  name='public_startups'),
    path('privacy/',    views.privacy_policy,   name='privacy'),
    path('terms/',      views.terms_conditions, name='terms'),
    path('nda/',        views.nda_policy,       name='nda_policy'),
]