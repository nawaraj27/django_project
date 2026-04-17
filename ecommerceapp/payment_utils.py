import hashlib
import hmac
import base64
import json
import requests
from django.conf import settings
from django.urls import reverse
import uuid
from datetime import datetime
from typing import Tuple, Optional

def generate_esewa_signature(secret_key: str, message: str) -> str:
    """
    Generate HMAC-SHA256 signature for eSewa payment
    """
    try:
        # Create HMAC-SHA256 hash
        hash_obj = hmac.new(
            secret_key.encode('utf-8'),
            message.encode('utf-8'),
            hashlib.sha256
        )
        # Return base64 encoded signature
        return base64.b64encode(hash_obj.digest()).decode('utf-8')
    except Exception as e:
        print(f"Error generating eSewa signature: {e}")
        return ""

def create_esewa_payment_data(amount: str, transaction_uuid: str, merchant_code: str, 
                             success_url: str, failure_url: str, secret_key: str) -> dict:
    """
    Create eSewa payment configuration
    """
    try:
        esewa_config = {
            'amount': amount,
            'tax_amount': '0',
            'total_amount': amount,
            'transaction_uuid': transaction_uuid,
            'product_code': merchant_code,
            'product_service_charge': '0',
            'product_delivery_charge': '0',
            'success_url': success_url,
            'failure_url': failure_url,
            'signed_field_names': 'total_amount,transaction_uuid,product_code',
        }
        
        # Generate signature string
        signature_string = f"total_amount={esewa_config['total_amount']},transaction_uuid={esewa_config['transaction_uuid']},product_code={esewa_config['product_code']}"
        
        # Generate signature
        signature = generate_esewa_signature(secret_key, signature_string)
        
        return {
            'config': esewa_config,
            'signature': signature,
            'signature_string': signature_string
        }
    except Exception as e:
        print(f"Error creating eSewa payment data: {e}")
        return {}

def initiate_khalti_payment(amount: str, purchase_order_id: str, purchase_order_name: str,
                           return_url: str, website_url: str, secret_key: str) -> dict:
    """
    Initiate Khalti payment and return payment URL
    """
    try:
        khalti_config = {
            'return_url': return_url,
            'website_url': website_url,
            'amount': int(float(amount) * 100),  # Convert to paisa
            'purchase_order_id': purchase_order_id,
            'purchase_order_name': purchase_order_name,
            'customer_info': {
                'name': 'Customer',
                'email': 'customer@example.com',
                'phone': '9800000000',
            }
        }
        
        # Make API call to Khalti
        response = requests.post(
            'https://a.khalti.com/api/v2/epayment/initiate/',
            headers={
                'Authorization': f'Key {secret_key}',
                'Content-Type': 'application/json',
            },
            json=khalti_config,
            timeout=30
        )
        
        if response.status_code == 200:
            khalti_response = response.json()
            return {
                'success': True,
                'payment_url': khalti_response.get('payment_url'),
                'khalti_response': khalti_response
            }
        else:
            error_data = response.json()
            return {
                'success': False,
                'error': f'Khalti API Error: {error_data}',
                'status_code': response.status_code
            }
            
    except requests.exceptions.RequestException as e:
        return {
            'success': False,
            'error': f'Network error: {str(e)}'
        }
    except Exception as e:
        return {
            'success': False,
            'error': f'Error initiating Khalti payment: {str(e)}'
        }

def generate_transaction_uuid() -> str:
    """
    Generate unique transaction UUID for payments
    """
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    unique_id = str(uuid.uuid4())[:8]
    return f"{timestamp}-{unique_id}"

def verify_esewa_payment(transaction_uuid: str, total_amount: str, 
                        product_code: str, signature: str, secret_key: str) -> bool:
    """
    Verify eSewa payment signature
    """
    try:
        # Recreate signature string
        signature_string = f"total_amount={total_amount},transaction_uuid={transaction_uuid},product_code={product_code}"
        
        # Generate expected signature
        expected_signature = generate_esewa_signature(secret_key, signature_string)
        
        # Compare signatures
        return hmac.compare_digest(signature, expected_signature)
    except Exception as e:
        print(f"Error verifying eSewa payment: {e}")
        return False

def get_payment_urls(request, payment_method: str) -> dict:
    """
    Get success and failure URLs for payment methods
    """
    base_url = request.build_absolute_uri('/')
    
    if payment_method == 'esewa':
        return {
            'success_url': f"{base_url}payment/success/?method=esewa",
            'failure_url': f"{base_url}payment/failure/?method=esewa"
        }
    elif payment_method == 'khalti':
        return {
            'success_url': f"{base_url}payment/success/?method=khalti",
            'failure_url': f"{base_url}payment/failure/?method=khalti"
        }
    
    return {
        'success_url': f"{base_url}payment/success/",
        'failure_url': f"{base_url}payment/failure/"
    }

def check_esewa_status(product_code: str, total_amount: str, transaction_uuid: str, *, production: bool = False) -> dict:
    """
    Query eSewa status API for a transaction.

    Returns parsed JSON on success or a dict with error on failure.
    """
    try:
        base_url = "https://epay.esewa.com.np" if production else "https://rc.esewa.com.np"
        url = (
            f"{base_url}/api/epay/transaction/status/"
            f"?product_code={product_code}"
            f"&total_amount={total_amount}"
            f"&transaction_uuid={transaction_uuid}"
        )
        resp = requests.get(url, timeout=30)
        if resp.status_code == 200:
            return {"success": True, "data": resp.json()}
        return {"success": False, "error": f"HTTP {resp.status_code}", "body": resp.text}
    except requests.exceptions.RequestException as e:
        return {"success": False, "error": f"Network error: {str(e)}"}
    except Exception as e:
        return {"success": False, "error": f"Unexpected error: {str(e)}"}

def parse_esewa_base64_response(encoded_body: str) -> Tuple[bool, Optional[dict], Optional[str]]:
    """
    Decode Base64 response body from eSewa into dict.

    Returns (ok, data, error)
    """
    try:
        decoded_bytes = base64.b64decode(encoded_body)
        data = json.loads(decoded_bytes.decode("utf-8"))
        return True, data, None
    except Exception as e:
        return False, None, str(e)
