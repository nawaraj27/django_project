from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User

# Create your tests here.

class CartCheckoutTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.username = 'tester'
        self.email = 'tester@example.com'
        self.password = 'testpass123'
        self.user = User.objects.create_user(username=self.username, email=self.email, password=self.password)
        self.client.login(username=self.username, password=self.password)

    def test_cart_add(self):
        # You must adjust the product id and exact url to match your project
        # Example: POST /add-to-cart/1/
        response = self.client.post('/add-to-cart/1/', {'quantity': 2})
        self.assertIn(response.status_code, [200, 302])
        # If your cart is stored in session, check
        cart = self.client.session.get('cart', {})
        self.assertTrue('1' in cart or '1' in str(cart))

    def test_cart_update(self):
        # Assumes item is already in cart
        self.client.post('/add-to-cart/1/', {'quantity': 2})
        response = self.client.post('/update-cart/1/', {'quantity': 5})
        self.assertIn(response.status_code, [200, 302])

    def test_cart_remove(self):
        self.client.post('/add-to-cart/1/', {'quantity': 2})
        response = self.client.post('/remove-from-cart/1/')
        self.assertIn(response.status_code, [200, 302])

    def test_checkout(self):
        self.client.post('/add-to-cart/1/', {'quantity': 2})
        response = self.client.post('/checkout/', {
            'first_name': 'Unit',
            'last_name': 'Test',
            'contact_number': '9800000000',
            'address': 'Test address',
            'payment_method': 'cash',
        })
        self.assertIn(response.status_code, [200, 302])
        # Add further validation (order count increases, etc) as needed
