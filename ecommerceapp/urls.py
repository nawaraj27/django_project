from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),  # changed from views.index
    path('contact', views.contactus, name='contact'),  # changed from views.contact
    path('contact', views.contactus, name='contact_capital'),  # same here
    path('about', views.about, name='about'),
    path('About', views.about, name='about_capital'),
    path('checkout/', views.checkout, name='checkout'),
    path('profile', views.profile, name='profile'),
    path('tracker', views.tracker, name='tracker'),
    path('test', views.test_page, name='test_page'),
    path('thank-you/<int:order_id>/', views.thank_you, name='thank_you'),
    path('cart/clear/', views.clear_cart, name='clear_cart'),
    
    # Payment Gateway URLs
    path('payment/choice', views.payment_choice, name='payment_choice'),
    path('payment/esewa', views.esewa_payment, name='esewa_payment'),
    path('payment/khalti', views.khalti_payment, name='khalti_payment'),
    path('payment/success', views.payment_success, name='payment_success'),
    path('payment/failure', views.payment_failure, name='payment_failure'),
    path('api/initiate-payment', views.initiate_payment, name='initiate_payment'),
    path('api/esewa/status', views.esewa_status, name='esewa_status'),
]
