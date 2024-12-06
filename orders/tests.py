from django.test import TestCase
from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from .models import Order, OrderItem, DeliveryZone
from products.models import Product, Category
from django.contrib.auth import get_user_model

User = get_user_model()

class OrderTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.category = Category.objects.create(
            name='Test Category',
            slug='test-category'
        )
        self.product = Product.objects.create(
            name='Test Product',
            slug='test-product',
            description='Test Description',
            price=99.99,
            category=self.category
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
        self.order_item = OrderItem.objects.create(
            order=self.order,
            product=self.product,
            quantity=2,
            price=self.product.price
        )

    def test_order_creation(self):
        """Test creating a new order"""
        self.assertEqual(self.order.user, self.user)
        self.assertEqual(self.order.status, 'pending')
        self.assertEqual(self.order.items.count(), 1)
        self.assertEqual(self.order_item.quantity, 2)

class OrderAPITests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
        self.category = Category.objects.create(
            name='Test Category',
            slug='test-category'
        )
        self.product = Product.objects.create(
            name='Test Product',
            slug='test-product',
            description='Test Description',
            price=99.99,
            category=self.category
        )
        self.delivery_zone = DeliveryZone.objects.create(
            name='Test Zone',
            delivery_fee=10.00,
            estimated_days=2
        )
        self.orders_url = reverse('orders:order-list')

    def test_create_order(self):
        """Test creating a new order through API"""
        data = {
            'delivery_zone': self.delivery_zone.id,
            'shipping_address': '123 Test St, Test City',
            'items': [{
                'product': self.product.id,
                'quantity': 2
            }]
        }
        response = self.client.post(self.orders_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Order.objects.count(), 1)
        self.assertEqual(OrderItem.objects.count(), 1)
