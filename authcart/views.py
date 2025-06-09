from django.shortcuts import render, redirect, HttpResponse
from django.contrib.auth.models import User
from django.views.generic import View
from django.utils.encoding import force_str, force_bytes
from django.contrib import messages
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.core.mail import EmailMessage
from django.conf import settings
from django.urls import reverse
from .utils import account_activation_token

def signup(request):
    if request.method == "POST":
        email = request.POST['email']
        password = request.POST['pass1']
        confirm_password = request.POST['pass2']

        if password != confirm_password:
            messages.warning(request, "Password is Not Matching")
            return render(request, 'signup.html') # Assuming signup.html is also in linGunGulili/templates/

        try:
            # Using filter and exists() is generally safer than get() followed by DoesNotExist for checking existence
            if User.objects.filter(username=email).exists():
                messages.info(request, "Email is Taken")
                return render(request, 'signup.html')
        except User.DoesNotExist: # This block is redundant if using filter().exists()
            pass # No action needed here if User.objects.filter(username=email).exists() handles the check

        # If email not taken, proceed to create user
        user = User.objects.create_user(email, email, password)
        user.is_active = False
        user.save()

        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = account_activation_token.make_token(user)

        email_subject = "Activate Your Account"
        # Assuming 'activate.html' is also in linGunGulili/templates/ or authcart/templates/authcart/
        message = render_to_string('activate.html', {
            'user': user,
            'domain': '127.0.0.1:8000', # Consider getting this from request.META['HTTP_HOST'] for production
            'uidb64': uid,
            'token': token,
        })

        email_message = EmailMessage(
            email_subject,
            message,
            settings.EMAIL_HOST_USER,
            [email]
        )
        email_message.send()
        messages.success(request, "Account created successfully")
        return redirect('/auth/login/') # Redirects to your login page

    return render(request, 'signup.html') # Renders signup form for GET request


class ActivateAccount(View):
    def get(self, request, uidb64, token):
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except Exception as identifier: # Catch a more specific exception if possible
            user = None

        if user is not None and account_activation_token.check_token(user, token):
            user.is_active = True
            user.save()
            messages.success(request, "Account activated successfully")
            return redirect('/auth/login/')
        # Assuming 'auth/activatefail.html' is in linGunGulili/templates/auth/
        return render(request, 'auth/activatefail.html')


def handlelogin(request):
    # This line now correctly points to linGunGulili/templates/login.html
    return render(request,'login.html')


def handlelogout(request):
    # Consider using django.contrib.auth.logout here if you haven't already
    # from django.contrib.auth import logout
    # logout(request)
    return redirect('/auth/login/')