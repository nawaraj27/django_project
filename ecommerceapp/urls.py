from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('contact', views.contact, name='contact'),
    path('Contact', views.contact, name='contact_capital'),
    path('about', views.about, name='about'),
    path('About', views.about, name='about_capital'),  # this handles /About
]
