from django.urls import path
from authcart import views
from django.contrib.auth import views as auth_views # This import is there but not used for login/logout in your code

urlpatterns = [
    path('signup/', views.signup, name='signup'),
    path('login/', views.handlelogin, name='handlelogin'),
    path('logout/', views.handlelogout, name='handlelogout'),
    path('activate/<uidb64>/<token>', views.ActivateAccount.as_view(), name='activate'),
]