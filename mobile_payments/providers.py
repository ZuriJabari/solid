"""
Mobile payment provider implementations.
"""
from django.utils import timezone
import uuid
from .models import MobilePaymentProvider

class PaymentError(Exception):
    """Custom exception for payment-related errors"""
    pass

class BaseProvider:
    """Base class for payment providers"""
    def __init__(self, provider_model):
        self.provider = provider_model

    def initiate_payment(self, payment):
        """Initiate a payment with the provider"""
        # In test environment, just update the status
        payment.status = 'PROCESSING'
        payment.provider_tx_ref = str(uuid.uuid4())
        payment.save()
        return {'status': 'success'}

    def check_payment_status(self, payment):
        """Check payment status with the provider"""
        # In test environment, just return the current status
        return {'status': payment.status}

    def validate_notification(self, payload, signature):
        """Validate webhook notification"""
        # In test environment, always return True
        return True

    def process_notification(self, notification):
        """Process webhook notification"""
        # In test environment, just mark the payment as successful
        payment = notification.payment
        payment.status = 'SUCCESSFUL'
        payment.save()
        
        notification.is_processed = True
        notification.processed_at = timezone.now()
        notification.save()

class MTNProvider(BaseProvider):
    """MTN Mobile Money provider implementation"""
    pass

class AirtelProvider(BaseProvider):
    """Airtel Money provider implementation"""
    pass

def get_provider(provider_code):
    """Get provider instance by code"""
    try:
        provider_model = MobilePaymentProvider.objects.get(
            code=provider_code,
            is_active=True
        )
        
        if provider_code == 'MTN':
            return MTNProvider(provider_model)
        elif provider_code == 'AIRTEL':
            return AirtelProvider(provider_model)
        else:
            raise PaymentError(f"Unsupported provider: {provider_code}")
            
    except MobilePaymentProvider.DoesNotExist:
        raise PaymentError(f"Provider not found: {provider_code}") 