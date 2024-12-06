from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from ..models import Order, DeliveryZone, PickupLocation, PaymentMethod
from decimal import Decimal

User = get_user_model()

class CheckoutAdminTests(TestCase):
    def setUp(self):
        self.client = Client()
        
        # Create admin user
        self.admin_user = User.objects.create_superuser(
            email='admin@test.com',
            password='testpass123'
        )
        self.client.login(email='admin@test.com', password='testpass123')
        
        # Create test data
        self.delivery_zone = DeliveryZone.objects.create(
            name='Test Zone',
            delivery_fee=Decimal('5.00'),
            estimated_days=2
        )
        
        self.pickup_location = PickupLocation.objects.create(
            name='Test Location',
            address='123 Test St',
            contact_phone='1234567890',
            operating_hours='9-5'
        )
        
        self.payment_method = PaymentMethod.objects.create(
            name='Test Payment',
            provider='TEST',
            min_amount=Decimal('0.00'),
            max_amount=Decimal('1000.00')
        )
        
        # Create some orders
        self.create_test_orders()

    def create_test_orders(self):
        """Create test orders with various statuses and dates"""
        statuses = ['pending', 'processing', 'completed', 'cancelled']
        delivery_methods = ['delivery', 'pickup']
        
        orders = []
        for i in range(10):
            order = Order.objects.create(
                user=self.admin_user,
                status=statuses[i % len(statuses)],
                total_amount=Decimal(f'{(i + 1) * 10}.00'),
                delivery_method=delivery_methods[i % len(delivery_methods)],
                delivery_zone=self.delivery_zone if i % 2 == 0 else None,
                pickup_location=self.pickup_location if i % 2 == 1 else None,
                payment_method=self.payment_method,
                created_at=timezone.now() - timedelta(days=i)
            )
            if order.status in ['completed', 'cancelled']:
                order.updated_at = order.created_at + timedelta(hours=2)
                order.save()
            orders.append(order)
        return orders

    def test_order_admin_list_view(self):
        """Test the order list view in admin"""
        url = reverse('admin:checkout_order_changelist')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Total Orders')
        self.assertContains(response, 'Total Revenue')
        self.assertContains(response, 'Success Rate')

    def test_order_admin_metrics_api(self):
        """Test the metrics API endpoint"""
        url = reverse('admin:order_metrics_api')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertIn('today_orders', data)
        self.assertIn('today_revenue', data)
        self.assertIn('pending_orders', data)
        self.assertIn('processing_orders', data)

    def test_delivery_zone_admin(self):
        """Test delivery zone admin features"""
        url = reverse('admin:checkout_deliveryzone_changelist')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Zone')
        self.assertContains(response, 'Total Orders')
        self.assertContains(response, 'Total Revenue')

    def test_pickup_location_admin(self):
        """Test pickup location admin features"""
        url = reverse('admin:checkout_pickuplocation_changelist')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Location')
        self.assertContains(response, 'Total Pickups')
        self.assertContains(response, 'Average Wait Time')

    def test_payment_method_admin(self):
        """Test payment method admin features"""
        url = reverse('admin:checkout_paymentmethod_changelist')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Payment')
        self.assertContains(response, 'Total Transactions')
        self.assertContains(response, 'Total Value')

    def test_order_admin_actions(self):
        """Test order admin actions"""
        url = reverse('admin:checkout_order_changelist')
        
        # Create a processing order
        order = Order.objects.create(
            user=self.admin_user,
            status='processing',
            total_amount=Decimal('100.00'),
            delivery_method='delivery',
            payment_method=self.payment_method
        )
        
        # Test marking orders as completed
        data = {
            'action': 'mark_as_completed',
            '_selected_action': [order.id]
        }
        response = self.client.post(url, data, follow=True)
        
        # Verify response and order status
        self.assertEqual(response.status_code, 200)
        order.refresh_from_db()
        self.assertEqual(order.status, 'completed')

    def test_export_csv_action(self):
        """Test CSV export functionality"""
        url = reverse('admin:checkout_order_changelist')
        
        data = {
            'action': 'export_orders_csv',
            '_selected_action': Order.objects.all().values_list('id', flat=True)
        }
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/csv')
        self.assertIn('attachment; filename="orders.csv"', response['Content-Disposition']) 