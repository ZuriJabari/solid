from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.utils.translation import gettext_lazy as _
import requests
import logging
from .models import MobilePayment

logger = logging.getLogger(__name__)

class PaymentNotificationService:
    """Service for sending payment notifications via email and SMS"""
    
    @staticmethod
    def send_payment_initiated_notification(payment: MobilePayment) -> None:
        """Send notification when payment is initiated"""
        try:
            # Email notification
            subject = _('Payment Initiated - Order #{order_id}').format(
                order_id=payment.order.id
            )
            
            context = {
                'user': payment.user,
                'payment': payment,
                'order': payment.order,
                'amount': payment.amount,
                'provider': payment.provider.name
            }
            
            html_message = render_to_string(
                'mobile_payments/email/payment_initiated.html',
                context
            )
            text_message = render_to_string(
                'mobile_payments/email/payment_initiated.txt',
                context
            )
            
            send_mail(
                subject=subject,
                message=text_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[payment.user.email],
                html_message=html_message
            )
            
            # SMS notification
            sms_message = _(
                'Payment of UGX {amount} initiated for order #{order_id}. '
                'Please check your phone for the payment prompt.'
            ).format(amount=payment.amount, order_id=payment.order.id)
            
            PaymentNotificationService.send_sms(
                phone_number=payment.phone_number,
                message=sms_message
            )
            
        except Exception as e:
            logger.error(f"Failed to send payment initiated notification: {str(e)}")
    
    @staticmethod
    def send_payment_status_notification(payment: MobilePayment) -> None:
        """Send notification when payment status changes"""
        try:
            # Email notification
            subject = _('Payment {status} - Order #{order_id}').format(
                status=payment.get_status_display(),
                order_id=payment.order.id
            )
            
            context = {
                'user': payment.user,
                'payment': payment,
                'order': payment.order,
                'amount': payment.amount,
                'provider': payment.provider.name,
                'status': payment.get_status_display()
            }
            
            html_message = render_to_string(
                'mobile_payments/email/payment_status.html',
                context
            )
            text_message = render_to_string(
                'mobile_payments/email/payment_status.txt',
                context
            )
            
            send_mail(
                subject=subject,
                message=text_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[payment.user.email],
                html_message=html_message
            )
            
            # SMS notification
            if payment.status in ['SUCCESSFUL', 'FAILED']:
                status_display = _('successful') if payment.status == 'SUCCESSFUL' else _('failed')
                sms_message = _(
                    'Payment of UGX {amount} for order #{order_id} was {status}. '
                    'Thank you for using our service.'
                ).format(
                    amount=payment.amount,
                    order_id=payment.order.id,
                    status=status_display
                )
                
                PaymentNotificationService.send_sms(
                    phone_number=payment.phone_number,
                    message=sms_message
                )
            
        except Exception as e:
            logger.error(f"Failed to send payment status notification: {str(e)}")
    
    @staticmethod
    def send_payment_reminder(payment: MobilePayment) -> None:
        """Send payment reminder notification"""
        try:
            # Email reminder
            subject = _('Payment Reminder - Order #{order_id}').format(
                order_id=payment.order.id
            )
            
            context = {
                'user': payment.user,
                'payment': payment,
                'order': payment.order,
                'amount': payment.amount,
                'provider': payment.provider.name
            }
            
            html_message = render_to_string(
                'mobile_payments/email/payment_reminder.html',
                context
            )
            text_message = render_to_string(
                'mobile_payments/email/payment_reminder.txt',
                context
            )
            
            send_mail(
                subject=subject,
                message=text_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[payment.user.email],
                html_message=html_message
            )
            
            # SMS reminder
            sms_message = _(
                'Reminder: Your payment of UGX {amount} for order #{order_id} is pending. '
                'Please complete the payment to avoid order cancellation.'
            ).format(amount=payment.amount, order_id=payment.order.id)
            
            PaymentNotificationService.send_sms(
                phone_number=payment.phone_number,
                message=sms_message
            )
            
        except Exception as e:
            logger.error(f"Failed to send payment reminder notification: {str(e)}")
    
    @staticmethod
    def send_sms(phone_number: str, message: str) -> bool:
        """Send SMS using Africa's Talking API"""
        try:
            # Remove any spaces or special characters from phone number
            cleaned_phone = ''.join(filter(str.isdigit, phone_number))
            
            # Add country code if not present
            if len(cleaned_phone) == 10:
                cleaned_phone = '256' + cleaned_phone[1:]
            
            headers = {
                'ApiKey': settings.AT_API_KEY,
                'Content-Type': 'application/x-www-form-urlencoded',
                'Accept': 'application/json'
            }
            
            data = {
                'username': settings.AT_USERNAME,
                'to': cleaned_phone,
                'message': message,
                'from': settings.AT_SENDER_ID
            }
            
            response = requests.post(
                'https://api.africastalking.com/version1/messaging',
                headers=headers,
                data=data
            )
            
            if response.status_code == 201:
                logger.info(f"SMS sent successfully to {phone_number}")
                return True
            else:
                logger.error(f"Failed to send SMS: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"SMS sending failed: {str(e)}")
            return False 