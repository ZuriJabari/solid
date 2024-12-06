from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from decimal import Decimal
from checkout.models import Order, DeliveryZone, PickupLocation, PaymentMethod

User = get_user_model()

class AdminTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_superuser(
            email='admin@example.com',
            password='testpass123'
        )
        self.client.force_login(self.user)
        
        self.delivery_zone = DeliveryZone.objects.create(
            name='Test Zone',
            delivery_fee=5000,
            estimated_days=2
        )
        
        self.pickup_location = PickupLocation.objects.create(
            name='Test Location',
            address='123 Test St',
            contact_phone='+256700000000'
        )
        
        self.payment_method = PaymentMethod.objects.create(
            name='Test Method',
            provider='MTN',
            min_amount=1000,
            max_amount=1000000
        )

    def test_delivery_zone_list(self):
        url = reverse('admin:checkout_deliveryzone_changelist')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Zone')
        self.assertContains(response, 'USh 5,000')

    def test_pickup_location_list(self):
        url = reverse('admin:checkout_pickuplocation_changelist')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Location')
        self.assertContains(response, '123 Test St')

    def test_payment_method_list(self):
        url = reverse('admin:checkout_paymentmethod_changelist')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Method')
        self.assertContains(response, 'USh 1,000')
        self.assertContains(response, 'USh 1,000,000') 