from rest_framework.test import APITestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from decimal import Decimal
from orders.models import CustomerOrder
from ..models import MobilePaymentProvider, MobilePayment, PaymentNotification

User = get_user_model()

class MobilePaymentProviderViewSetTests(APITestCase):
    def setUp(self):
        # First, print initial state
        print("\nInitial providers:", MobilePaymentProvider.objects.all().values_list('name', 'is_active'))
        
        # Delete all providers
        MobilePaymentProvider.objects.all().delete()
        
        # Verify deletion
        print("After deletion:", MobilePaymentProvider.objects.all().count())
        
        # Create user and authenticate
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
        
        # Create one active provider
        self.active_provider = MobilePaymentProvider.objects.create(
            name='MTN Mobile Money',
            code='MTN',
            is_active=True,
            api_base_url='https://sandbox.momodeveloper.mtn.com',
            api_key='test_api_key',
            api_secret='test_api_secret',
            webhook_secret='test_webhook_secret'
        )
        
        # Create inactive provider for testing
        self.inactive_provider = MobilePaymentProvider.objects.create(
            name='Inactive Provider',
            code='INACTIVE',
            is_active=False,
            api_base_url='https://example.com',
            api_key='test_api_key',
            api_secret='test_api_secret',
            webhook_secret='test_webhook_secret'
        )
        
        # Verify final setup state
        print("After setup:", MobilePaymentProvider.objects.all().values_list('name', 'is_active'))
        
        self.list_url = reverse('mobile_payments:provider-list')
        self.detail_url = reverse('mobile_payments:provider-detail', args=[self.active_provider.id])

    def test_list_providers(self):
        """Test listing payment providers"""
        # Print all providers before the test
        print("\nAll providers before test:", MobilePaymentProvider.objects.all().values_list('name', 'is_active'))
        
        # Get list of providers
        response = self.client.get(self.list_url)
        
        # Print response data
        print("Response data:", response.data)
        
        # Get active providers from database
        active_providers = MobilePaymentProvider.objects.filter(is_active=True)
        print("Active providers:", active_providers.values_list('name', 'is_active'))
        
        # Verify response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), active_providers.count())
        
        # First provider should be our test provider
        provider_data = response.data['results'][0]
        self.assertEqual(provider_data['name'], self.active_provider.name)
        self.assertEqual(provider_data['code'], self.active_provider.code)
        self.assertTrue(provider_data['is_active'])

    def test_retrieve_provider(self):
        """Test retrieving a specific provider"""
        response = self.client.get(self.detail_url)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['name'], self.active_provider.name)
        self.assertEqual(response.data['code'], self.active_provider.code)
        self.assertTrue(response.data['is_active'])

class MobilePaymentViewSetTests(APITestCase):
    def setUp(self):
        # Create user and authenticate
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
        
        # Clear any existing data
        MobilePaymentProvider.objects.all().delete()
        MobilePayment.objects.all().delete()
        
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
        
        # Create order
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
        
        # Create URLs
        self.initiate_url = reverse('mobile_payments:payment-initiate')
        self.check_status_url = reverse('mobile_payments:payment-check-status')

    def test_initiate_payment(self):
        """Test initiating a payment"""
        data = {
            'order_id': str(self.order.id),
            'provider_code': 'MTN',
            'phone_number': '256771234567'
        }
        response = self.client.post(self.initiate_url, data, format='json')
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('payment', response.data)
        self.assertEqual(response.data['payment']['status'], 'PROCESSING')

    def test_check_payment_status(self):
        """Test checking payment status"""
        # Create a payment first
        payment = MobilePayment.objects.create(
            user=self.user,
            order=self.order,
            provider=self.provider,
            amount=Decimal('100.00'),
            currency='UGX',
            phone_number='256771234567',
            provider_tx_ref='test_tx_ref'
        )
        
        data = {
            'provider_tx_ref': 'test_tx_ref'
        }
        response = self.client.post(self.check_status_url, data, format='json')
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('payment', response.data)
        self.assertEqual(response.data['payment']['status'], 'PENDING')

class PaymentWebhookViewTests(APITestCase):
    def setUp(self):
        # Create user
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        
        # Clear any existing data
        MobilePaymentProvider.objects.all().delete()
        MobilePayment.objects.all().delete()
        PaymentNotification.objects.all().delete()
        
        # Create providers
        self.mtn_provider = MobilePaymentProvider.objects.create(
            name='MTN Mobile Money',
            code='MTN',
            is_active=True,
            api_base_url='https://sandbox.momodeveloper.mtn.com',
            api_key='test_api_key',
            api_secret='test_api_secret',
            webhook_secret='test_webhook_secret'
        )
        
        self.airtel_provider = MobilePaymentProvider.objects.create(
            name='Airtel Money',
            code='AIRTEL',
            is_active=True,
            api_base_url='https://openapiuat.airtel.africa',
            api_key='test_api_key',
            api_secret='test_api_secret',
            webhook_secret='test_webhook_secret'
        )
        
        # Create order
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
        
        # Create payments
        self.mtn_payment = MobilePayment.objects.create(
            user=self.user,
            order=self.order,
            provider=self.mtn_provider,
            amount=Decimal('100.00'),
            currency='UGX',
            phone_number='256771234567',
            provider_tx_ref='test_tx_ref'
        )
        
        self.airtel_payment = MobilePayment.objects.create(
            user=self.user,
            order=self.order,
            provider=self.airtel_provider,
            amount=Decimal('100.00'),
            currency='UGX',
            phone_number='256771234567',
            provider_tx_ref='test_tx_ref_airtel'
        )
        
        # Create URLs
        self.mtn_webhook_url = reverse('mobile_payments:webhook-mtn')
        self.airtel_webhook_url = reverse('mobile_payments:webhook-airtel')

    def test_mtn_webhook(self):
        """Test MTN webhook endpoint"""
        data = {
            'status': 'SUCCESSFUL',
            'referenceId': 'test_tx_ref'
        }
        response = self.client.post(
            self.mtn_webhook_url,
            data,
            format='json',
            HTTP_X_SIGNATURE='test_signature'
        )
        
        self.assertEqual(response.status_code, 200)
        self.mtn_payment.refresh_from_db()
        self.assertEqual(self.mtn_payment.status, 'SUCCESSFUL')

    def test_airtel_webhook(self):
        """Test Airtel webhook endpoint"""
        data = {
            'transaction': {
                'id': 'test_tx_ref_airtel',
                'status': 'SUCCESS'
            }
        }
        response = self.client.post(
            self.airtel_webhook_url,
            data,
            format='json',
            HTTP_X_AUTH_TOKEN='test_token'
        )
        
        self.assertEqual(response.status_code, 200)
        self.airtel_payment.refresh_from_db()
        self.assertEqual(self.airtel_payment.status, 'SUCCESSFUL') 