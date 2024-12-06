from django.utils.translation import gettext_lazy as _
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils import timezone
import requests
import json
import uuid
import logging
from decimal import Decimal
from .models import MobilePayment, MobilePaymentProvider, PaymentNotification
from .notifications import PaymentNotificationService
from orders.models import Order

logger = logging.getLogger(__name__)

class PaymentValidationError(ValidationError):
    pass

class PaymentProcessingError(Exception):
    pass

class MobilePaymentService:
    """Service class for handling mobile money payments"""
    
    MAX_RETRIES = 3
    RETRY_DELAY = 60  # seconds
    
    def __init__(self, provider):
        self.provider = provider
    
    def validate_payment(self, order: Order, phone_number: str) -> None:
        """Validate payment details before processing"""
        if not order:
            raise PaymentValidationError(_('Order is required'))
            
        if not phone_number:
            raise PaymentValidationError(_('Phone number is required'))
            
        # Validate amount is within provider limits
        if order.total < Decimal('100'):
            raise PaymentValidationError(_('Amount is below minimum allowed (UGX 100)'))
            
        if order.total > Decimal('5000000'):
            raise PaymentValidationError(_('Amount exceeds maximum allowed (UGX 5,000,000)'))
            
        # Validate phone number format
        if not self._validate_phone_number(phone_number):
            raise PaymentValidationError(_('Invalid phone number format'))
            
        # Check if order already has a pending payment
        if MobilePayment.objects.filter(
            order=order,
            status__in=['PENDING', 'PROCESSING']
        ).exists():
            raise PaymentValidationError(_('Order already has a pending payment'))
    
    def initiate_payment(self, order: Order, phone_number: str) -> MobilePayment:
        """Initiate a new mobile money payment"""
        try:
            # Validate payment details
            self.validate_payment(order, phone_number)
            
            # Create payment record
            payment = MobilePayment.objects.create(
                user=order.user,
                order=order,
                provider=self.provider,
                amount=order.total,
                phone_number=phone_number,
                transaction_id=self._generate_transaction_id()
            )
            
            # Call provider API
            response = self._call_provider_api(payment)
            
            # Update payment with provider response
            payment.provider_reference = response.get('provider_reference')
            payment.provider_response = response
            payment.status = 'PROCESSING'
            payment.save()
            
            # Create notification for tracking
            PaymentNotification.objects.create(
                payment=payment,
                provider=self.provider,
                notification_type='INITIATION',
                payload=response
            )
            
            # Send notifications
            PaymentNotificationService.send_payment_initiated_notification(payment)
            
            return payment
            
        except PaymentValidationError:
            raise
        except Exception as e:
            logger.error(f"Payment initiation failed: {str(e)}", exc_info=True)
            raise PaymentProcessingError(_('Payment initiation failed. Please try again.'))
    
    def check_payment_status(self, payment: MobilePayment) -> dict:
        """Check payment status with provider"""
        try:
            response = self._call_provider_status_api(payment)
            
            # Update payment status based on provider response
            new_status = self._map_provider_status(response.get('status'))
            if new_status != payment.status:
                payment.status = new_status
                payment.save()
                
                # Create notification for status change
                PaymentNotification.objects.create(
                    payment=payment,
                    provider=self.provider,
                    notification_type='STATUS_UPDATE',
                    payload=response
                )
                
                # Send notifications for final statuses
                if new_status in ['SUCCESSFUL', 'FAILED']:
                    PaymentNotificationService.send_payment_status_notification(payment)
            
            return {
                'status': payment.status,
                'provider_reference': payment.provider_reference,
                'last_checked': timezone.now()
            }
            
        except Exception as e:
            logger.error(f"Status check failed: {str(e)}", exc_info=True)
            raise PaymentProcessingError(_('Unable to check payment status'))
    
    def handle_webhook(self, payload: dict) -> None:
        """Handle webhook notifications from provider"""
        try:
            transaction_id = payload.get('transaction_id')
            if not transaction_id:
                raise ValueError('Missing transaction ID in webhook payload')
                
            payment = MobilePayment.objects.get(transaction_id=transaction_id)
            
            # Create notification record
            notification = PaymentNotification.objects.create(
                payment=payment,
                provider=self.provider,
                notification_type='WEBHOOK',
                payload=payload
            )
            
            # Update payment status
            new_status = self._map_provider_status(payload.get('status'))
            if new_status != payment.status:
                payment.status = new_status
                payment.save()
                
                # Send notifications for final statuses
                if new_status in ['SUCCESSFUL', 'FAILED']:
                    PaymentNotificationService.send_payment_status_notification(payment)
            
            notification.processed = True
            notification.save()
            
        except MobilePayment.DoesNotExist:
            logger.error(f"Payment not found for webhook: {transaction_id}")
        except Exception as e:
            logger.error(f"Webhook processing failed: {str(e)}", exc_info=True)
    
    def retry_failed_payment(self, payment: MobilePayment) -> bool:
        """Retry a failed payment"""
        if payment.status != 'FAILED':
            return False
            
        # Check retry count
        retry_count = PaymentNotification.objects.filter(
            payment=payment,
            notification_type='RETRY'
        ).count()
        
        if retry_count >= self.MAX_RETRIES:
            return False
        
        try:
            # Call provider API again
            response = self._call_provider_api(payment)
            
            # Update payment
            payment.provider_reference = response.get('provider_reference')
            payment.provider_response = response
            payment.status = 'PROCESSING'
            payment.save()
            
            # Create retry notification
            PaymentNotification.objects.create(
                payment=payment,
                provider=self.provider,
                notification_type='RETRY',
                payload=response
            )
            
            # Send payment initiated notification
            PaymentNotificationService.send_payment_initiated_notification(payment)
            
            return True
            
        except Exception as e:
            logger.error(f"Payment retry failed: {str(e)}", exc_info=True)
            return False
    
    def send_payment_reminder(self, payment: MobilePayment) -> None:
        """Send payment reminder for pending payments"""
        if payment.status not in ['PENDING', 'PROCESSING']:
            return
            
        try:
            PaymentNotificationService.send_payment_reminder(payment)
            
            # Create reminder notification
            PaymentNotification.objects.create(
                payment=payment,
                provider=self.provider,
                notification_type='REMINDER',
                payload={'sent_at': timezone.now().isoformat()}
            )
            
        except Exception as e:
            logger.error(f"Failed to send payment reminder: {str(e)}", exc_info=True)
    
    def _validate_phone_number(self, phone_number: str) -> bool:
        """Validate phone number format"""
        # Remove any spaces or special characters
        cleaned = ''.join(filter(str.isdigit, phone_number))
        
        # Check if it's a valid Uganda phone number
        if len(cleaned) != 10 and len(cleaned) != 12:
            return False
            
        # Check prefix for Uganda numbers
        if len(cleaned) == 10 and not cleaned.startswith(('077', '078', '076')):
            return False
            
        if len(cleaned) == 12 and not cleaned.startswith(('25677', '25678', '25676')):
            return False
            
        return True
    
    def _generate_transaction_id(self) -> str:
        """Generate unique transaction ID"""
        return f"MP-{uuid.uuid4().hex[:12].upper()}"
    
    def _call_provider_api(self, payment: MobilePayment) -> dict:
        """Call provider API to initiate payment"""
        if self.provider.code == 'MTN':
            return self._call_mtn_api(payment)
        elif self.provider.code == 'AIRTEL':
            return self._call_airtel_api(payment)
        else:
            raise ValueError(f"Unsupported provider: {self.provider.code}")
    
    def _call_provider_status_api(self, payment: MobilePayment) -> dict:
        """Call provider API to check payment status"""
        if self.provider.code == 'MTN':
            return self._call_mtn_status_api(payment)
        elif self.provider.code == 'AIRTEL':
            return self._call_airtel_status_api(payment)
        else:
            raise ValueError(f"Unsupported provider: {self.provider.code}")
    
    def _map_provider_status(self, provider_status: str) -> str:
        """Map provider status to internal status"""
        status_mapping = {
            # MTN statuses
            'PENDING': 'PENDING',
            'PROCESSING': 'PROCESSING',
            'SUCCESSFUL': 'SUCCESSFUL',
            'FAILED': 'FAILED',
            'CANCELLED': 'CANCELLED',
            # Airtel statuses
            'INITIATED': 'PENDING',
            'IN_PROGRESS': 'PROCESSING',
            'SUCCESS': 'SUCCESSFUL',
            'FAILURE': 'FAILED',
            'TIMEOUT': 'FAILED',
        }
        return status_mapping.get(provider_status, 'FAILED')
    
    def _call_mtn_api(self, payment: MobilePayment) -> dict:
        """Call MTN Mobile Money API"""
        headers = {
            'Authorization': f"Bearer {self.provider.api_key}",
            'X-Reference-Id': payment.transaction_id,
            'X-Target-Environment': 'sandbox',
            'Content-Type': 'application/json'
        }
        
        payload = {
            'amount': str(payment.amount),
            'currency': 'UGX',
            'externalId': payment.transaction_id,
            'payer': {
                'partyIdType': 'MSISDN',
                'partyId': payment.phone_number
            },
            'payerMessage': f'Payment for order {payment.order.id}',
            'payeeNote': f'Payment from {payment.user.get_full_name()}'
        }
        
        response = requests.post(
            f"{self.provider.api_base_url}/collection/v1_0/requesttopay",
            headers=headers,
            json=payload
        )
        
        if response.status_code not in (200, 201, 202):
            raise PaymentProcessingError(f"MTN API error: {response.text}")
            
        return response.json()
    
    def _call_airtel_api(self, payment: MobilePayment) -> dict:
        """Call Airtel Money API"""
        headers = {
            'Authorization': f"Bearer {self.provider.api_key}",
            'Content-Type': 'application/json'
        }
        
        payload = {
            'reference': payment.transaction_id,
            'subscriber': {
                'country': 'UG',
                'currency': 'UGX',
                'msisdn': payment.phone_number
            },
            'transaction': {
                'amount': str(payment.amount),
                'country': 'UG',
                'currency': 'UGX',
                'id': payment.transaction_id
            }
        }
        
        response = requests.post(
            f"{self.provider.api_base_url}/merchant/v1/payments/",
            headers=headers,
            json=payload
        )
        
        if response.status_code not in (200, 201, 202):
            raise PaymentProcessingError(f"Airtel API error: {response.text}")
            
        return response.json()
    
    def _call_mtn_status_api(self, payment: MobilePayment) -> dict:
        """Check payment status with MTN API"""
        headers = {
            'Authorization': f"Bearer {self.provider.api_key}",
            'X-Target-Environment': 'sandbox'
        }
        
        response = requests.get(
            f"{self.provider.api_base_url}/collection/v1_0/requesttopay/{payment.transaction_id}",
            headers=headers
        )
        
        if response.status_code != 200:
            raise PaymentProcessingError(f"MTN status check failed: {response.text}")
            
        return response.json()
    
    def _call_airtel_status_api(self, payment: MobilePayment) -> dict:
        """Check payment status with Airtel API"""
        headers = {
            'Authorization': f"Bearer {self.provider.api_key}"
        }
        
        response = requests.get(
            f"{self.provider.api_base_url}/standard/v1/payments/{payment.transaction_id}",
            headers=headers
        )
        
        if response.status_code != 200:
            raise PaymentProcessingError(f"Airtel status check failed: {response.text}")
            
        return response.json() 