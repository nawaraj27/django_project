from django.shortcuts import render, HttpResponse, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from .models import Product, Contact, Orders, OrderUpdate
from math import ceil
import json
from django.views.decorators.csrf import csrf_exempt
from .payment_utils import (
    create_esewa_payment_data,
    initiate_khalti_payment,
    generate_transaction_uuid,
    verify_esewa_payment,
    get_payment_urls,
    parse_esewa_base64_response,
    check_esewa_status
)
from .models import PaymentTransaction, EsewaPayment, KhaltiPayment
import os
import base64
from decimal import Decimal
from django.contrib.admin.views.decorators import staff_member_required


# Home Page
def home(request):
    current_user = request.user
    print(current_user)

    allProds = []
    catprods = Product.objects.values('category', 'id')
    cats = {item['category'] for item in catprods}

    for cat in cats:
        prod = Product.objects.filter(category=cat)
        n = len(prod)
        nSlides = n // 4 + ceil((n / 4) - (n // 4))
        allProds.append([prod, range(1, nSlides), nSlides])

    return render(request, 'index.html', {'allProds': allProds})


def about(request):
    return render(request, 'about.html')


@login_required
def contactus(request):
    if request.method == "POST":
        name = request.POST.get('name', '')
        email = request.POST.get('email', '')
        phone = request.POST.get('phone', '')
        desc = request.POST.get('desc', '')

        contact = Contact(name=name, email=email, phone=phone, desc=desc)
        contact.save()
        messages.success(request, "Contact Form is Submitted")

    return render(request, 'contact.html')


@login_required
def profile(request):
    """User profile page showing account information and order history"""
    user = request.user
    # Get user's order history
    orders = Orders.objects.filter(email=user.email).order_by('-timestamp')

    context = {
        'user': user,
        'orders': orders,
    }
    return render(request, 'profile.html', context)

def tracker(request):
    """Order tracking page"""
    if request.method == "POST":
        orderId = request.POST.get('orderId', '')
        email = request.POST.get('email', '')
        
        try:
            # Find the order
            order = Orders.objects.filter(order_id=orderId, email=email).first()
            
            if order:
                # Get order updates
                updates = OrderUpdate.objects.filter(order_id=orderId).order_by('-timestamp')
                
                context = {
                    'order': order,
                    'updates': updates,
                    'found': True
                }
                return render(request, 'tracker.html', context)
            else:
                messages.error(request, 'Order not found. Please check your Order ID and Email.')
                return render(request, 'tracker.html', {'found': False})
                
        except Exception as e:
            messages.error(request, f'Error tracking order: {str(e)}')
            return render(request, 'tracker.html', {'found': False})
    
    return render(request, 'tracker.html', {'found': False})

@staff_member_required
def test_page(request):
    """Test page for UI components"""
    return render(request, 'test.html')


def productView(request, myid):
    product = Product.objects.filter(id=myid).first()
    return render(request, 'prodView.html', {'product': product})


@login_required
def checkout(request):
    if request.method == "POST":
        items_json = request.POST.get('itemsJson', '')
        name = request.POST.get('name', '')
        amount_raw = request.POST.get('amt')
        try:
            amount = Decimal(amount_raw)
        except:
            amount = Decimal(0)
        email = request.POST.get('email', '')
        address1 = request.POST.get('address1', '')
        address2 = request.POST.get('address2', '')
        city = request.POST.get('city', '')
        state = request.POST.get('state', '')
        phone = request.POST.get('phone', '')

        order = Orders(
            items_json=items_json,
            name=name,
            amount=amount,
            email=email,
            address1=address1,
            address2=address2,
            city=city,
            state=state,
            phone=phone
        )
        order.save()
        update = OrderUpdate(order_id=order.order_id, update_desc="The order has been placed")
        update.save()
        # Thank you handled on dedicated page with payment link and order id
        return redirect('thank_you', order_id=order.order_id)
    return render(request, 'checkout.html')


def thank_you(request, order_id):
    """Show thank you message and payment options with current order ID."""
    order = Orders.objects.get(order_id=order_id)
    try:
        cart = json.loads(order.items_json)
    except Exception:
        cart = {}
    return render(request, 'thank_you.html', {'order': order, 'cart': cart})


@csrf_exempt
def handlerequest(request):
    # This will just handle a simulated payment status
    return render(request, 'paymentstatus.html', {
        'response': {
            'RESPCODE': '01',
            'RESPMSG': 'Payment simulated - success'
        }
    })


def handlelogin(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('pass1')
        user = authenticate(username=email, password=password)

        if user is not None:
            login(request, user)
            messages.info(request, "Successfully Logged In")
            return redirect('/')
        else:
            messages.error(request, "Invalid Credentials")
            return redirect('/login')

    return render(request, 'login.html')


def signup(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        pass1 = request.POST.get('pass1')
        pass2 = request.POST.get('pass2')

        if pass1 != pass2:
            messages.error(request, "Passwords do not match, please try again!")
            return redirect('/signup')

        if User.objects.filter(username=email).exists() or User.objects.filter(email=email).exists():
            messages.warning(request, "Email already exists")
            return redirect('/signup')

        user = User.objects.create_user(email, email, pass1)
        user.save()
        messages.info(request, 'Thanks for signing up')
        return redirect('/login')

    return render(request, "signup.html")


def logouts(request):
    logout(request)
    messages.warning(request, "Logout Success")
    return render(request, 'login.html')

# Payment Gateway Views
def initiate_payment(request):
    """Initiate payment for eSewa or Khalti"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            payment_method = data.get('method')
            amount = data.get('amount')
            product_name = data.get('productName')
            transaction_id = data.get('transactionId')

            if not all([payment_method, amount, product_name, transaction_id]):
                return HttpResponse(
                    json.dumps({'error': 'Missing required fields'}),
                    content_type='application/json',
                    status=400
                )

            # Generate unique transaction UUID
            transaction_uuid = generate_transaction_uuid()

            if payment_method == 'esewa':
                # eSewa payment initiation
                esewa_merchant_code = os.getenv('ESEWA_MERCHANT_CODE', 'EPAYTEST')
                esewa_secret_key = os.getenv('ESEWA_SECRET_KEY', '8gBm/:&EnhH.1/q')

                # Get payment URLs
                urls = get_payment_urls(request, 'esewa')

                # Create eSewa payment data
                esewa_data = create_esewa_payment_data(
                    amount=amount,
                    transaction_uuid=transaction_uuid,
                    merchant_code=esewa_merchant_code,
                    success_url=urls['success_url'],
                    failure_url=urls['failure_url'],
                    secret_key=esewa_secret_key
                )

                if esewa_data:
                    return HttpResponse(
                        json.dumps({
                            'amount': amount,
                            'esewaConfig': {
                                **esewa_data['config'],
                                'signature': esewa_data['signature'],
                                'product_service_charge': 0,
                                'product_delivery_charge': 0,
                                'tax_amount': 0,
                                'total_amount': float(amount)
                            }
                        }),
                        content_type='application/json'
                    )
                else:
                    return HttpResponse(
                        json.dumps({'error': 'Failed to create eSewa payment data'}),
                        content_type='application/json',
                        status=500
                    )

            elif payment_method == 'khalti':
                # Khalti payment initiation
                khalti_secret_key = os.getenv('KHALTI_SECRET_KEY', 'test_secret_key')

                # Get payment URLs
                urls = get_payment_urls(request, 'khalti')

                # Initiate Khalti payment
                khalti_result = initiate_khalti_payment(
                    amount=amount,
                    purchase_order_id=transaction_id,
                    purchase_order_name=product_name,
                    return_url=urls['success_url'],
                    website_url=request.build_absolute_uri('/'),
                    secret_key=khalti_secret_key
                )

                if khalti_result['success']:
                    return HttpResponse(
                        json.dumps({
                            'khaltiPaymentUrl': khalti_result['payment_url']
                        }),
                        content_type='application/json'
                    )
                else:
                    return HttpResponse(
                        json.dumps({'error': khalti_result['error']}),
                        content_type='application/json',
                        status=500
                    )
            else:
                return HttpResponse(
                    json.dumps({'error': 'Invalid payment method'}),
                    content_type='application/json',
                    status=400
                )

        except json.JSONDecodeError:
            return HttpResponse(
                json.dumps({'error': 'Invalid JSON data'}),
                content_type='application/json',
                status=400
            )
        except Exception as e:
            return HttpResponse(
                json.dumps({'error': f'Payment initiation failed: {str(e)}'}),
                content_type='application/json',
                status=500
            )

    return HttpResponse(
        json.dumps({'error': 'Method not allowed'}),
        content_type='application/json',
        status=405
    )

def payment_success(request):
    # Clear cart upon payment success
    if request.user.is_authenticated:
        # If you use a Cart model linked to user, clear it here
        if 'cart' in request.session:
            del request.session['cart']
    else:
        request.session['cart'] = {}
    messages.success(request, "Payment successful! Cart cleared.")
    # Direct user to home page or payment_success.html. Let JS handle cart localStorage sync via cleared=1 param.
    return redirect('/cart/?cleared=1')

def payment_failure(request):
    """Handle failed payment callback"""
    payment_method = request.GET.get('method', '')

    if payment_method == 'esewa':
        messages.error(request, "eSewa payment failed!")
    elif payment_method == 'khalti':
        messages.error(request, "Khalti payment failed!")
    else:
        messages.error(request, "Payment failed!")

    return redirect('/')

@csrf_exempt
def esewa_status(request):
    """Status check endpoint to query eSewa when no immediate response is received"""
    if request.method not in ['GET', 'POST']:
        return HttpResponse(json.dumps({"error": "Method not allowed"}), content_type='application/json', status=405)

    # Accept JSON or form
    product_code = request.GET.get('product_code') or request.POST.get('product_code')
    total_amount = request.GET.get('total_amount') or request.POST.get('total_amount')
    transaction_uuid = request.GET.get('transaction_uuid') or request.POST.get('transaction_uuid')
    production = (request.GET.get('env') == 'prod') or (request.POST.get('env') == 'prod')

    if not all([product_code, total_amount, transaction_uuid]):
        return HttpResponse(
            json.dumps({"error": "Missing product_code, total_amount or transaction_uuid"}),
            content_type='application/json',
            status=400
        )

    result = check_esewa_status(product_code, total_amount, transaction_uuid, production=production)
    return HttpResponse(json.dumps(result), content_type='application/json', status=200 if result.get('success') else 502)

def payment_choice(request):
    """Display payment method selection page"""
    return render(request, 'payment_choice.html')

def esewa_payment(request):
    """eSewa payment form or direct processing when amount is provided."""
    if request.method == 'POST':
        amount = request.POST.get('amount')
        product_name = request.POST.get('productName')
        transaction_id = request.POST.get('transactionId')

        if all([amount, product_name, transaction_id]):
            # Generate transaction UUID
            transaction_uuid = generate_transaction_uuid()

            # Get eSewa configuration
            esewa_merchant_code = os.getenv('ESEWA_MERCHANT_CODE', 'EPAYTEST')
            esewa_secret_key = os.getenv('ESEWA_SECRET_KEY', '8gBm/:&EnhH.1/q')

            # Get payment URLs
            urls = get_payment_urls(request, 'esewa')

            # Create eSewa payment data
            esewa_data = create_esewa_payment_data(
                amount=amount,
                transaction_uuid=transaction_uuid,
                merchant_code=esewa_merchant_code,
                success_url=urls['success_url'],
                failure_url=urls['failure_url'],
                secret_key=esewa_secret_key
            )

            if esewa_data:
                context = {
                    'esewa_config': esewa_data['config'],
                    'signature': esewa_data['signature'],
                    'amount': amount
                }
                return render(request, 'esewa_payment.html', context)
            else:
                messages.error(request, "Failed to create eSewa payment")
                return redirect('payment_choice')
        else:
            messages.error(request, "Please fill all required fields")
            return redirect('payment_choice')

    # Handle GET with amount -> show amount only and proceed directly
    amount_get = request.GET.get('amount')
    if amount_get:
        esewa_merchant_code = os.getenv('ESEWA_MERCHANT_CODE', 'EPAYTEST')
        esewa_secret_key = os.getenv('ESEWA_SECRET_KEY', '8gBm/:&EnhH.1/q')
        urls = get_payment_urls(request, 'esewa')
        transaction_uuid = generate_transaction_uuid()
        esewa_data = create_esewa_payment_data(
            amount=amount_get,
            transaction_uuid=transaction_uuid,
            merchant_code=esewa_merchant_code,
            success_url=urls['success_url'],
            failure_url=urls['failure_url'],
            secret_key=esewa_secret_key
        )
        if esewa_data:
            context = {
                'esewa_config': esewa_data['config'],
                'signature': esewa_data['signature'],
                'amount': amount_get
            }
            return render(request, 'esewa_payment.html', context)
        messages.error(request, "Failed to prepare eSewa payment")
        return redirect('payment_choice')

    return render(request, 'esewa_payment_form.html')

def khalti_payment(request):
    """Khalti payment form"""
    if request.method == 'POST':
        amount = request.POST.get('amount')
        product_name = request.POST.get('productName')
        transaction_id = request.POST.get('transactionId')

        if all([amount, product_name, transaction_id]):
            # Get Khalti configuration
            khalti_secret_key = os.getenv('KHALTI_SECRET_KEY', 'test_secret_key')

            # Get payment URLs
            urls = get_payment_urls(request, 'khalti')

            # Initiate Khalti payment
            khalti_result = initiate_khalti_payment(
                amount=amount,
                purchase_order_id=transaction_id,
                purchase_order_name=product_name,
                return_url=urls['success_url'],
                website_url=request.build_absolute_uri('/'),
                secret_key=khalti_secret_key
            )

            if khalti_result['success']:
                return redirect(khalti_result['payment_url'])
            else:
                messages.error(request, f"Khalti payment failed: {khalti_result['error']}")
                return redirect('payment_choice')
        else:
            messages.error(request, "Please fill all required fields")
            return redirect('payment_choice')

    return render(request, 'khalti_payment_form.html')

def clear_cart(request):
    if request.user.is_authenticated:
        # If you have a Cart model, use Cart.objects.filter(user=request.user).delete()
        if 'cart' in request.session:
            del request.session['cart']
    else:
        request.session['cart'] = {}
    messages.success(request, "Cart cleared successfully.")
    # Add cleared=1 param so frontend knows to clear localStorage too
    return redirect('/cart/?cleared=1')
