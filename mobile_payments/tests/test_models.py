from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from decimal import Decimal
from orders.models import CustomerOrder
from ..models import MobilePaymentProvider, MobilePayment, PaymentNotification

User = get_user_model()

class MobilePaymentProviderTests(TestCase):
    def setUp(self):
        self.provider_data = {
            'name': 'MTN Mobile Money',
            'code': 'MTN',
            'is_active': True,
            'api_base_url': 'https://sandbox.momodeveloper.mtn.com',
            'api_key': 'test_api_key',
            'api_secret': 'test_api_secret',
            'webhook_secret': 'test_webhook_secret'
        }
        self.provider = MobilePaymentProvider.objects.create(**self.provider_data)

    def test_create_provider(self):
        """Test creating a payment provider"""
        self.assertEqual(self.provider.name, self.provider_data['name'])
        self.assertEqual(self.provider.code, self.provider_data['code'])
        self.assertTrue(self.provider.is_active)

    def test_provider_str(self):
        """Test the provider string representation"""
        self.assertEqual(str(self.provider), self.provider_data['name'])

class MobilePaymentTests(TestCase):
    def setUp(self):
        # Create user
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        
        # Create provider
        self.provider = MobilePaymentProvider.objects.create(
            name='MTN Mobile Money',
            code='MTN',
            is_active=True,
            api_base_url='https://sandbox.momodeveloper.mtn.com',
            api_key='test_api_key',
            api_secret='test_api_secret',
            webhook_secret='test_webhook_secret'
        )
        
        # Create order with all required fields
        self.order = CustomerOrder.objects.create(
            user=self.user,
            shipping_address='123 Test St',
            billing_address='123 Test St',
            phone='256771234567',
            email='test@example.com',
            subtotal=Decimal('100.00'),
            shipping_cost=Decimal('10.00'),
            tax=Decimal('15.00'),
            total=Decimal('125.00')
        )
        
        # Create payment
        self.payment = MobilePayment.objects.create(
            user=self.user,
            order=self.order,
            provider=self.provider,
            amount=Decimal('100.00'),
            currency='UGX',
            phone_number='256771234567',
            provider_tx_ref='test_tx_ref'
        )

    def test_create_payment(self):
        """Test creating a payment"""
        self.assertEqual(self.payment.user, self.user)
        self.assertEqual(self.payment.provider, self.provider)
        self.assertEqual(self.payment.amount, Decimal('100.00'))
        self.assertEqual(self.payment.status, 'PENDING')

    def test_payment_str(self):
        """Test the payment string representation"""
        expected = f"{self.provider.name} payment of {self.payment.amount} {self.payment.currency} for order {self.order.id}"
        self.assertEqual(str(self.payment), expected)

    def test_payment_status_transition(self):
        """Test payment status transitions"""
        self.payment.status = 'PROCESSING'
        self.payment.save()
        self.assertEqual(self.payment.status, 'PROCESSING')
        
        self.payment.status = 'SUCCESSFUL'
        self.payment.save()
        self.assertEqual(self.payment.status, 'SUCCESSFUL')
        self.assertIsNotNone(self.payment.completed_at)

class PaymentNotificationTests(TestCase):
    def setUp(self):
        # Create user
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        
        # Create provider
        self.provider = MobilePaymentProvider.objects.create(
            name='MTN Mobile Money',
            code='MTN',
            is_active=True,
            api_base_url='https://sandbox.momodeveloper.mtn.com',
            api_key='test_api_key',
            api_secret='test_api_secret',
            webhook_secret='test_webhook_secret'
        )
        
        # Create order with all required fields
        self.order = CustomerOrder.objects.create(
            user=self.user,
            shipping_address='123 Test St',
            billing_address='123 Test St',
            phone='256771234567',
            email='test@example.com',
            subtotal=Decimal('100.00'),
            shipping_cost=Decimal('10.00'),
            tax=Decimal('15.00'),
            total=Decimal('125.00')
        )
        
        # Create payment
        self.payment = MobilePayment.objects.create(
            user=self.user,
            order=self.order,
            provider=self.provider,
            amount=Decimal('100.00'),
            currency='UGX',
            phone_number='256771234567',
            provider_tx_ref='test_tx_ref'
        )
        
        # Create notification
        self.notification = PaymentNotification.objects.create(
            payment=self.payment,
            provider=self.provider,
            notification_type='PAYMENT_STATUS',
            status='SUCCESSFUL',
            raw_payload={'status': 'SUCCESSFUL'}
        )

    def test_create_notification(self):
        """Test creating a payment notification"""
        self.assertEqual(self.notification.payment, self.payment)
        self.assertEqual(self.notification.provider, self.provider)
        self.assertEqual(self.notification.notification_type, 'PAYMENT_STATUS')
        self.assertFalse(self.notification.is_processed)

    def test_notification_str(self):
        """Test the notification string representation"""
        expected = f"{self.notification.notification_type} notification for payment {self.payment.id}"
        self.assertEqual(str(self.notification), expected)

    def test_notification_processing(self):
        """Test notification processing status"""
        self.notification.is_processed = True
        self.notification.processed_at = timezone.now()
        self.notification.save()
        
        self.assertTrue(self.notification.is_processed)
        self.assertIsNotNone(self.notification.processed_at) 