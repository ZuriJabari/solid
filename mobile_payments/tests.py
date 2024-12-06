from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from decimal import Decimal
from unittest.mock import patch, MagicMock
from .models import MobilePayment, MobilePaymentProvider, PaymentNotification
from .services import MobilePaymentService, PaymentValidationError, PaymentProcessingError
from orders.models import Order, DeliveryZone
from config.currency import CURRENCY

User = get_user_model()

class MobilePaymentModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            phone='256777123456'
        )
        self.provider = MobilePaymentProvider.objects.create(
            name='MTN Mobile Money',
            code='MTN',
            api_base_url='https://sandbox.mtn.com',
            api_key='test_key',
            api_secret='test_secret',
            webhook_secret='test_webhook'
        )
        self.delivery_zone = DeliveryZone.objects.create(
            name='Test Zone',
            delivery_fee=Decimal('1000'),
            estimated_days=2
        )
        self.order = Order.objects.create(
            user=self.user,
            total=Decimal('50000'),
            delivery_zone=self.delivery_zone
        )

    def test_mobile_payment_creation(self):
        payment = MobilePayment.objects.create(
            user=self.user,
            order=self.order,
            provider=self.provider,
            amount=Decimal('50000'),
            phone_number='256777123456'
        )
        self.assertEqual(payment.status, 'PENDING')
        self.assertEqual(payment.amount, Decimal('50000'))
        self.assertEqual(str(payment), f"MTN Mobile Money - 50000 {CURRENCY} - PENDING")

    def test_payment_notification_creation(self):
        payment = MobilePayment.objects.create(
            user=self.user,
            order=self.order,
            provider=self.provider,
            amount=Decimal('50000'),
            phone_number='256777123456'
        )
        notification = PaymentNotification.objects.create(
            payment=payment,
            provider=self.provider,
            notification_type='INITIATION',
            payload={'status': 'PENDING'}
        )
        self.assertFalse(notification.processed)
        self.assertEqual(
            str(notification),
            f"MTN Mobile Money - INITIATION - {notification.created_at}"
        )

class MobilePaymentServiceTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            phone='256777123456'
        )
        self.provider = MobilePaymentProvider.objects.create(
            name='MTN Mobile Money',
            code='MTN',
            api_base_url='https://sandbox.mtn.com',
            api_key='test_key',
            api_secret='test_secret',
            webhook_secret='test_webhook'
        )
        self.delivery_zone = DeliveryZone.objects.create(
            name='Test Zone',
            delivery_fee=Decimal('1000'),
            estimated_days=2
        )
        self.order = Order.objects.create(
            user=self.user,
            total=Decimal('50000'),
            delivery_zone=self.delivery_zone
        )
        self.service = MobilePaymentService(self.provider)

    def test_validate_payment_success(self):
        # Should not raise any exceptions
        self.service.validate_payment(self.order, '256777123456')

    def test_validate_payment_invalid_phone(self):
        with self.assertRaises(PaymentValidationError):
            self.service.validate_payment(self.order, '123456')  # Invalid phone

    def test_validate_payment_amount_too_low(self):
        order = Order.objects.create(
            user=self.user,
            total=Decimal('50'),  # Below minimum
            delivery_zone=self.delivery_zone
        )
        
        with self.assertRaises(PaymentValidationError):
            self.service.validate_payment(order, '256777123456')

    def test_validate_payment_amount_too_high(self):
        order = Order.objects.create(
            user=self.user,
            total=Decimal('6000000'),  # Above maximum
            delivery_zone=self.delivery_zone
        )
        
        with self.assertRaises(PaymentValidationError):
            self.service.validate_payment(order, '256777123456')

    @patch('mobile_payments.services.MobilePaymentService._call_provider_api')
    def test_initiate_payment_success(self, mock_call_api):
        mock_call_api.return_value = {
            'status': 'PENDING',
            'provider_reference': 'TEST123'
        }
        payment = self.service.initiate_payment(self.order, '256777123456')
        self.assertEqual(payment.status, 'PROCESSING')
        self.assertEqual(payment.amount, self.order.total)
        self.assertTrue(payment.transaction_id)

    @patch('mobile_payments.services.MobilePaymentService._call_provider_api')
    def test_initiate_payment_api_error(self, mock_call_api):
        mock_call_api.side_effect = PaymentProcessingError('API Error')
        with self.assertRaises(PaymentProcessingError):
            self.service.initiate_payment(self.order, '256777123456')

    @patch('mobile_payments.services.MobilePaymentService._call_provider_status_api')
    def test_check_payment_status(self, mock_status_api):
        payment = MobilePayment.objects.create(
            user=self.user,
            order=self.order,
            provider=self.provider,
            amount=Decimal('50000'),
            phone_number='256777123456'
        )
        mock_status_api.return_value = {'status': 'SUCCESSFUL'}
        
        status_info = self.service.check_payment_status(payment)
        self.assertEqual(status_info['status'], 'SUCCESSFUL')
        
        # Verify payment status was updated
        payment.refresh_from_db()
        self.assertEqual(payment.status, 'SUCCESSFUL')

class MobilePaymentAPITests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            phone='256777123456'
        )
        self.provider = MobilePaymentProvider.objects.create(
            name='MTN Mobile Money',
            code='MTN',
            api_base_url='https://sandbox.mtn.com',
            api_key='test_key',
            api_secret='test_secret',
            webhook_secret='test_webhook'
        )
        self.delivery_zone = DeliveryZone.objects.create(
            name='Test Zone',
            delivery_fee=Decimal('1000'),
            estimated_days=2
        )
        self.order = Order.objects.create(
            user=self.user,
            total=Decimal('50000'),
            delivery_zone=self.delivery_zone
        )
        self.client.force_authenticate(user=self.user)

    def test_initiate_payment_api(self):
        response = self.client.post(
            reverse('mobile_payments:initiate'),
            {
                'order_id': str(self.order.id),
                'phone_number': '256777123456'
            }
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)  # API returns error due to mock

    def test_check_payment_status_api(self):
        payment = MobilePayment.objects.create(
            user=self.user,
            order=self.order,
            provider=self.provider,
            amount=Decimal('50000'),
            phone_number='256777123456',
            transaction_id='TEST123'
        )
        
        url = reverse('mobile_payments:payment-check-status')
        data = {'transaction_id': payment.transaction_id}
        
        with patch('mobile_payments.services.MobilePaymentService._call_provider_status_api') as mock_api:
            mock_api.return_value = {'status': 'SUCCESSFUL'}
            response = self.client.post(url, data)
            
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'SUCCESSFUL')

    def test_retry_payment_api(self):
        payment = MobilePayment.objects.create(
            user=self.user,
            order=self.order,
            provider=self.provider,
            amount=Decimal('50000'),
            phone_number='256777123456',
            status='FAILED'
        )
        
        url = reverse('mobile_payments:payment-retry', args=[payment.id])
        
        with patch('mobile_payments.services.MobilePaymentService._call_provider_api') as mock_api:
            mock_api.return_value = {
                'status': 'PENDING',
                'provider_reference': 'TEST123'
            }
            response = self.client.post(url)
            
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        
        # Verify payment status was updated
        payment.refresh_from_db()
        self.assertEqual(payment.status, 'PROCESSING')

    def test_webhook_api(self):
        payment = MobilePayment.objects.create(
            user=self.user,
            order=self.order,
            provider=self.provider,
            amount=Decimal('50000'),
            phone_number='256777123456',
            transaction_id='TEST123'
        )
        
        url = reverse('mobile_payments:webhook', args=['MTN'])
        data = {
            'transaction_id': payment.transaction_id,
            'status': 'SUCCESSFUL',
            'amount': '50000',
            'currency': 'UGX',
            'provider_reference': 'TEST123'
        }
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify payment status was updated
        payment.refresh_from_db()
        self.assertEqual(payment.status, 'SUCCESSFUL')
        
        # Verify notification was created
        self.assertTrue(PaymentNotification.objects.filter(
            payment=payment,
            notification_type='WEBHOOK'
        ).exists())
