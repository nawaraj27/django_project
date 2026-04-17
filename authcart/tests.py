from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User

# Create your tests here.

class AuthenticationTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.signup_url = reverse('signup')
        self.login_url = reverse('handlelogin')
        self.logout_url = reverse('handlelogout')
        self.username = 'testuser'
        self.email = 'test@example.com'
        self.password = 'strongpw123'

    def test_signup(self):
        response = self.client.post(self.signup_url, {
            'username': self.username,
            'email': self.email,
            'pass1': self.password,
            'pass2': self.password
        })
        self.assertRedirects(response, self.login_url)
        self.assertTrue(User.objects.filter(username=self.username).exists())
        self.assertTrue(User.objects.filter(email=self.email).exists())
        user = User.objects.get(username=self.username)
        self.assertTrue(user.check_password(self.password))

    def test_login(self):
        User.objects.create_user(username=self.username, email=self.email, password=self.password)
        login = self.client.post(self.login_url, {'email': self.username, 'pass1': self.password})
        self.assertEqual(login.status_code, 302)  # Should redirect on success
        self.assertIn('_auth_user_id', self.client.session)

    def test_logout(self):
        user = User.objects.create_user(username=self.username, email=self.email, password=self.password)
        self.client.login(username=self.username, password=self.password)
        response = self.client.get(self.logout_url)
        self.assertRedirects(response, self.login_url)
        self.assertNotIn('_auth_user_id', self.client.session)
