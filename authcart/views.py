from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.views.generic import View
from django.utils.encoding import force_str, force_bytes
from django.contrib import messages
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.core.mail import EmailMessage
from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from .utils import account_activation_token


def signup(request):
    if request.method == "POST":
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('pass1')
        confirm_password = request.POST.get('pass2')

        if not username or not email or not password or not confirm_password:
            messages.warning(request, "All fields are required.")
            return render(request, 'signup.html')

        if password != confirm_password:
            messages.warning(request, "Passwords do not match.")
            return render(request, 'signup.html')

        if len(password) < 8:
            messages.warning(request, "Password must be at least 8 characters long.")
            return render(request, 'signup.html')

        # Email and username uniqueness check
        from django.core.validators import validate_email
        from django.core.exceptions import ValidationError
        try:
            validate_email(email)
        except ValidationError:
            messages.warning(request, "Enter a valid email address.")
            return render(request, 'signup.html')

        if User.objects.filter(username=username).exists():
            messages.info(request, "Username is already taken.")
            return render(request, 'signup.html')

        if User.objects.filter(email=email).exists():
            messages.info(request, "Email is already taken.")
            return render(request, 'signup.html')

        user = User.objects.create_user(username=username, email=email, password=password)
        user.is_active = True
        user.save()
        messages.success(request, "Account created successfully! You can now log in.")
        return redirect('/auth/login/')

    return render(request, 'signup.html')


class ActivateAccount(View):
    def get(self, request, uidb64, token):
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            user = None

        if user is not None and account_activation_token.check_token(user, token):
            user.is_active = True
            user.save()
            messages.success(request, "Your account has been activated successfully! You can now log in.")
            return redirect('/auth/login/')
        else:
            messages.error(request, "Account activation link is invalid or has expired.")
            return render(request, 'auth/activatefail.html')


def handlelogin(request):
    if request.method == 'POST':
        email_or_username = request.POST.get('email')
        password = request.POST.get('pass1')
        remember = request.POST.get('remember', None)

        user = authenticate(request, username=email_or_username, password=password)
        if user is None:
            # Try authenticating with email if not found as username
            from django.contrib.auth.models import User
            try:
                usr = User.objects.get(email=email_or_username)
                user = authenticate(request, username=usr.username, password=password)
            except User.DoesNotExist:
                user = None
        if user is not None:
            login(request, user)
            if not remember:
                request.session.set_expiry(0)  # Session expires on browser close if Remember Me not checked
            messages.success(request, 'You are logged in')
            return redirect('/')
        else:
            messages.info(request, 'Username/Email or Password is incorrect')
            return redirect('/auth/login/')
    return render(request, 'login.html')


def handlelogout(request):
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect('/auth/login/')


