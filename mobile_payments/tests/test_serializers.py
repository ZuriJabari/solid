from django.test import TestCase
from django.contrib.auth import get_user_model
from decimal import Decimal
from orders.models import CustomerOrder
from ..models import MobilePaymentProvider, MobilePayment, PaymentNotification
from ..serializers import (
    MobilePaymentProviderSerializer, MobilePaymentSerializer,
    PaymentNotificationSerializer, InitiatePaymentSerializer,
    CheckPaymentStatusSerializer
)

User = get_user_model()

class MobilePaymentProviderSerializerTests(TestCase):
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
        self.serializer = MobilePaymentProviderSerializer(instance=self.provider)

    def test_contains_expected_fields(self):
        """Test that serializer contains expected fields"""
        data = self.serializer.data
        self.assertCountEqual(
            data.keys(),
            ['id', 'name', 'code', 'is_active']
        )

class MobilePaymentSerializerTests(TestCase):
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
        self.serializer = MobilePaymentSerializer(instance=self.payment)

    def test_contains_expected_fields(self):
        """Test that serializer contains expected fields"""
        data = self.serializer.data
        self.assertCountEqual(
            data.keys(),
            ['id', 'provider', 'provider_name', 'amount',
             'currency', 'phone_number', 'status',
             'provider_tx_id', 'provider_tx_ref',
             'created_at', 'completed_at']
        )

class InitiatePaymentSerializerTests(TestCase):
    def setUp(self):
        self.provider = MobilePaymentProvider.objects.create(
            name='MTN Mobile Money',
            code='MTN',
            is_active=True,
            api_base_url='https://sandbox.momodeveloper.mtn.com',
            api_key='test_api_key',
            api_secret='test_api_secret',
            webhook_secret='test_webhook_secret'
        )
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
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

    def test_valid_data(self):
        """Test serializer with valid data"""
        data = {
            'order_id': str(self.order.id),
            'provider_code': 'MTN',
            'phone_number': '256771234567'
        }
        serializer = InitiatePaymentSerializer(data=data)
        self.assertTrue(serializer.is_valid())

    def test_invalid_provider_code(self):
        """Test serializer with invalid provider code"""
        data = {
            'order_id': str(self.order.id),
            'provider_code': 'INVALID',
            'phone_number': '256771234567'
        }
        serializer = InitiatePaymentSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('provider_code', serializer.errors)

class CheckPaymentStatusSerializerTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.provider = MobilePaymentProvider.objects.create(
            name='MTN Mobile Money',
            code='MTN',
            is_active=True,
            api_base_url='https://sandbox.momodeveloper.mtn.com',
            api_key='test_api_key',
            api_secret='test_api_secret',
            webhook_secret='test_webhook_secret'
        )
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
        self.payment = MobilePayment.objects.create(
            user=self.user,
            order=self.order,
            provider=self.provider,
            amount=Decimal('100.00'),
            currency='UGX',
            phone_number='256771234567',
            provider_tx_ref='test_tx_ref'
        )

    def test_valid_data(self):
        """Test serializer with valid data"""
        data = {
            'provider_tx_ref': 'test_tx_ref'
        }
        serializer = CheckPaymentStatusSerializer(data=data)
        self.assertTrue(serializer.is_valid())

    def test_invalid_reference(self):
        """Test serializer with invalid transaction reference"""
        data = {
            'provider_tx_ref': 'invalid_ref'
        }
        serializer = CheckPaymentStatusSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('provider_tx_ref', serializer.errors) 