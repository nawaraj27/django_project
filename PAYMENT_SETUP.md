# eSewa and Khalti Payment Gateway Integration

This Django application now includes integrated payment gateways for eSewa and Khalti, two popular Nepali payment methods.

## Features

- **eSewa Integration**: Complete payment flow with HMAC-SHA256 signature verification
- **Khalti Integration**: Direct API integration with Khalti payment gateway
- **Secure Processing**: All sensitive operations handled server-side
- **Test Environment**: Ready-to-use test credentials for development
- **Responsive UI**: Modern, mobile-friendly payment forms

## Setup Instructions

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Environment Variables

Create a `.env` file in your project root with the following variables:

```env
# eSewa Configuration
ESEWA_MERCHANT_CODE=EPAYTEST
ESEWA_SECRET_KEY=8gBm/:&EnhH.1/q

# Khalti Configuration
KHALTI_SECRET_KEY=your_khalti_secret_key_here

# Django Configuration
SECRET_KEY=your_django_secret_key
DEBUG=True
```

### 3. Database Migration

```bash
python manage.py makemigrations
python manage.py migrate
```

### 4. Run the Application

```bash
python manage.py runserver
```

## Test Credentials

### eSewa Test Environment

- **Merchant Code**: EPAYTEST
- **Secret Key**: 8gBm/:&EnhH.1/q
- **Test IDs**: 9806800001, 9806800002, 9806800003, 9806800004, 9806800005
- **Password**: Nepal@123
- **MPIN**: 1122
- **Token**: 123456

### Khalti Test Environment

- **Test IDs**: 9800000000, 9800000001, 9800000002, 9800000003, 9800000004, 9800000005
- **MPIN**: 1111
- **OTP**: 987654

## API Endpoints

### Payment Initiation
- **URL**: `/api/initiate-payment`
- **Method**: POST
- **Content-Type**: application/json

**Request Body:**
```json
{
    "method": "esewa|khalti",
    "amount": "1000.00",
    "productName": "Product Name",
    "transactionId": "TXN123456"
}
```

### Payment Forms
- **Payment Choice**: `/payment/choice`
- **eSewa Form**: `/payment/esewa`
- **Khalti Form**: `/payment/khalti`

### Callback URLs
- **Success**: `/payment/success?method=esewa|khalti`
- **Failure**: `/payment/failure?method=esewa|khalti`

## Payment Flow

### eSewa Payment Flow
1. User fills payment form
2. System generates HMAC-SHA256 signature
3. Form auto-submits to eSewa gateway
4. User completes payment on eSewa
5. eSewa redirects to success/failure URL
6. System verifies payment signature

### Khalti Payment Flow
1. User fills payment form
2. System calls Khalti API
3. Khalti returns payment URL
4. User redirected to Khalti payment page
5. User completes payment
6. Khalti redirects to success/failure URL

## Security Features

- **HMAC-SHA256 Signatures**: eSewa payments verified cryptographically
- **Server-side Processing**: All sensitive operations handled securely
- **Environment Variables**: API keys stored securely
- **Input Validation**: Comprehensive form validation
- **CSRF Protection**: Django's built-in CSRF protection

## Customization

### Adding New Payment Methods
1. Create new model in `models.py`
2. Add utility functions in `payment_utils.py`
3. Create views in `views.py`
4. Add URLs in `urls.py`
5. Create templates in `templates/` directory

### Styling
- All payment forms use Bootstrap 5
- Custom CSS classes for payment-specific styling
- Responsive design for mobile devices
- Consistent color scheme across payment methods

## Production Deployment

### Environment Variables
- Update with production API keys
- Use production merchant codes
- Set `DEBUG=False`
- Use strong `SECRET_KEY`

### SSL Certificate
- HTTPS required for production
- Update callback URLs to use HTTPS
- Ensure secure cookie settings

### Database
- Use production database (PostgreSQL recommended)
- Regular backups
- Monitor payment transaction logs

## Troubleshooting

### Common Issues

1. **Payment Initiation Fails**
   - Check environment variables
   - Verify API endpoints
   - Check network connectivity

2. **Signature Verification Fails**
   - Verify secret key
   - Check field order in signature string
   - Ensure proper encoding

3. **Callback Issues**
   - Verify callback URLs
   - Check CSRF settings
   - Ensure proper redirect handling

### Debug Mode
Enable debug mode to see detailed error messages:
```python
DEBUG = True
```

## Support

For technical support or questions:
- Check Django documentation
- Review payment gateway documentation
- Test with provided test credentials
- Monitor Django logs for errors

## License

This integration is provided as-is for educational and development purposes. Ensure compliance with payment gateway terms of service and local regulations.
