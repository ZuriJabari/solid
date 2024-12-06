from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase
from datetime import timedelta
from decimal import Decimal
from django.contrib.auth import get_user_model
from .models import DeliveryZone, PickupLocation, PaymentMethod, CheckoutSession
from cart.models import Cart, CartItem
from products.models import Product, Category

User = get_user_model()

class CheckoutModelsTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        
        # Create test delivery zone
        self.delivery_zone = DeliveryZone.objects.create(
            name='Test Zone',
            description='Test delivery zone',
            delivery_fee=Decimal('5.00'),
            estimated_days=2
        )
        
        # Create test pickup location
        self.pickup_location = PickupLocation.objects.create(
            name='Test Store',
            address='123 Test St',
            contact_phone='1234567890',
            operating_hours='9 AM - 5 PM'
        )
        
        # Create test payment method
        self.payment_method = PaymentMethod.objects.create(
            name='Test Payment',
            provider='CARD',
            description='Test payment method'
        )

    def test_delivery_zone_creation(self):
        self.assertEqual(self.delivery_zone.name, 'Test Zone')
        self.assertEqual(self.delivery_zone.delivery_fee, Decimal('5.00'))
        self.assertTrue(self.delivery_zone.is_active)

    def test_pickup_location_creation(self):
        self.assertEqual(self.pickup_location.name, 'Test Store')
        self.assertEqual(self.pickup_location.contact_phone, '1234567890')
        self.assertTrue(self.pickup_location.is_active)

    def test_payment_method_creation(self):
        self.assertEqual(self.payment_method.name, 'Test Payment')
        self.assertEqual(self.payment_method.provider, 'CARD')
        self.assertTrue(self.payment_method.is_active)

class CheckoutAPITest(APITestCase):
    def setUp(self):
        # Create test user
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
        
        # Create test category
        self.category = Category.objects.create(
            name='Test Category',
            description='Test Category Description'
        )
        
        # Create test product
        self.product = Product.objects.create(
            name='Test Product',
            description='Test Description',
            price=Decimal('10.00'),
            category=self.category
        )
        
        # Create test cart with items
        self.cart = Cart.objects.create(user=self.user)
        self.cart_item = CartItem.objects.create(
            cart=self.cart,
            product=self.product,
            quantity=2
        )
        
        # Create test delivery zone
        self.delivery_zone = DeliveryZone.objects.create(
            name='Test Zone',
            description='Test delivery zone',
            delivery_fee=Decimal('5.00'),
            estimated_days=2
        )
        
        # Create test pickup location
        self.pickup_location = PickupLocation.objects.create(
            name='Test Store',
            address='123 Test St',
            contact_phone='1234567890',
            operating_hours='9 AM - 5 PM'
        )
        
        # Create test payment method
        self.payment_method = PaymentMethod.objects.create(
            name='Test Payment',
            provider='CARD',
            description='Test payment method'
        )

    def test_list_delivery_zones(self):
        url = reverse('checkout:delivery-zone-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], 'Test Zone')

    def test_list_pickup_locations(self):
        url = reverse('checkout:pickup-location-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], 'Test Store')

    def test_list_payment_methods(self):
        url = reverse('checkout:payment-method-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], 'Test Payment')

    def test_create_delivery_checkout_session(self):
        url = reverse('checkout:session-list')
        data = {
            'delivery_type': 'DELIVERY',
            'delivery_zone_id': self.delivery_zone.id,
            'delivery_address': '123 Test St',
            'delivery_instructions': 'Leave at door',
            'payment_method_id': self.payment_method.id
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['delivery_type'], 'DELIVERY')
        self.assertEqual(response.data['status'], 'PENDING')

    def test_create_pickup_checkout_session(self):
        url = reverse('checkout:session-list')
        data = {
            'delivery_type': 'PICKUP',
            'pickup_location_id': self.pickup_location.id,
            'payment_method_id': self.payment_method.id
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['delivery_type'], 'PICKUP')
        self.assertEqual(response.data['status'], 'PENDING')

    def test_confirm_checkout_session(self):
        # Create a checkout session
        session = CheckoutSession.objects.create(
            user=self.user,
            cart=self.cart,
            delivery_type='DELIVERY',
            delivery_zone=self.delivery_zone,
            delivery_address='123 Test St',
            payment_method=self.payment_method,
            subtotal=Decimal('20.00'),
            delivery_fee=Decimal('5.00'),
            total=Decimal('25.00'),
            expires_at=timezone.now() + timedelta(minutes=30)
        )
        
        url = reverse('checkout:session-confirm', args=[session.id])
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Refresh session from db
        session.refresh_from_db()
        self.assertEqual(session.status, 'PAYMENT_PENDING')

    def test_cancel_checkout_session(self):
        # Create a checkout session
        session = CheckoutSession.objects.create(
            user=self.user,
            cart=self.cart,
            delivery_type='DELIVERY',
            delivery_zone=self.delivery_zone,
            delivery_address='123 Test St',
            payment_method=self.payment_method,
            subtotal=Decimal('20.00'),
            delivery_fee=Decimal('5.00'),
            total=Decimal('25.00'),
            expires_at=timezone.now() + timedelta(minutes=30)
        )
        
        url = reverse('checkout:session-cancel', args=[session.id])
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Refresh session from db
        session.refresh_from_db()
        self.assertEqual(session.status, 'CANCELLED')

    def test_expired_session_handling(self):
        # Create an expired checkout session
        session = CheckoutSession.objects.create(
            user=self.user,
            cart=self.cart,
            delivery_type='DELIVERY',
            delivery_zone=self.delivery_zone,
            delivery_address='123 Test St',
            payment_method=self.payment_method,
            subtotal=Decimal('20.00'),
            delivery_fee=Decimal('5.00'),
            total=Decimal('25.00'),
            expires_at=timezone.now() - timedelta(minutes=1)
        )
        
        url = reverse('checkout:session-confirm', args=[session.id])
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Refresh session from db
        session.refresh_from_db()
        self.assertEqual(session.status, 'EXPIRED')
