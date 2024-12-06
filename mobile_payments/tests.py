from django.test import TestCase
from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from .models import MobilePaymentProvider, MobilePayment
from orders.models import Order, DeliveryZone
from django.contrib.auth import get_user_model

User = get_user_model()

class MobilePaymentTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.provider = MobilePaymentProvider.objects.create(
            name='Test Provider',
            code='TEST',
            api_key='test_key',
            api_secret='test_secret'
        )
        self.delivery_zone = DeliveryZone.objects.create(
            name='Test Zone',
            delivery_fee=10.00,
            estimated_days=2
        )
        self.order = Order.objects.create(
            user=self.user,
            delivery_zone=self.delivery_zone,
            status='pending'
        )
        self.payment = MobilePayment.objects.create(
            user=self.user,
            order=self.order,
            provider='TEST',
            amount=100.00,
            phone_number='+256700000000',
            status='PENDING'
        )

    def test_payment_creation(self):
        """Test creating a new mobile payment"""
        self.assertEqual(self.payment.user, self.user)
        self.assertEqual(self.payment.provider, 'TEST')
        self.assertEqual(self.payment.amount, 100.00)
        self.assertEqual(self.payment.status, 'PENDING')

class MobilePaymentAPITests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
        self.provider = MobilePaymentProvider.objects.create(
            name='Test Provider',
            code='TEST',
            api_key='test_key',
            api_secret='test_secret'
        )
        self.delivery_zone = DeliveryZone.objects.create(
            name='Test Zone',
            delivery_fee=10.00,
            estimated_days=2
        )
        self.order = Order.objects.create(
            user=self.user,
            delivery_zone=self.delivery_zone,
            status='pending'
        )
        self.initiate_payment_url = reverse('mobile_payments:payment-initiate')

    def test_initiate_payment(self):
        """Test initiating a mobile payment"""
        data = {
            'order_id': str(self.order.id),
            'provider': 'MTN',
            'phone_number': '+256700000000',
            'amount': '100.00'
        }
        response = self.client.post(self.initiate_payment_url, data)
        if response.status_code != status.HTTP_200_OK:
            print("Response data:", response.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('status', response.data)
        self.assertEqual(MobilePayment.objects.count(), 1)
