from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APITestCase
from rest_framework import status
from decimal import Decimal
from datetime import timedelta
from .models import (
    SalesMetric, InventoryMetric,
    CustomerMetric, ProductPerformance
)
from products.models import Product, Category
from orders.models import Order

User = get_user_model()

class AnalyticsModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_superuser(
            email='admin@example.com',
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
            price=Decimal('99.99'),
            category=self.category
        )
        
        # Create test metrics
        self.sales_metric = SalesMetric.objects.create(
            date=timezone.now().date(),
            total_sales=Decimal('999.99'),
            order_count=10,
            average_order_value=Decimal('99.99')
        )
        
        self.inventory_metric = InventoryMetric.objects.create(
            date=timezone.now().date(),
            metrics_data={
                str(self.product.id): {
                    'product_name': self.product.name,
                    'opening_stock': 100,
                    'current_stock': 90,
                    'units_sold': 10
                }
            }
        )
        
        self.customer_metric = CustomerMetric.objects.create(
            date=timezone.now().date(),
            total_customers=100,
            new_customers=20,
            returning_customers=80,
            cart_abandonment_rate=15.5
        )
        
        self.product_performance = ProductPerformance.objects.create(
            date=timezone.now().date(),
            product=self.product,
            views=1000,
            add_to_cart_count=50,
            purchase_count=30,
            revenue=Decimal('2999.70'),
            conversion_rate=3.0
        )

    def test_sales_metric_str(self):
        """Test the string representation of SalesMetric"""
        self.assertEqual(
            str(self.sales_metric),
            f"Sales Metrics for {self.sales_metric.date}"
        )

    def test_inventory_metric_str(self):
        """Test the string representation of InventoryMetric"""
        self.assertEqual(
            str(self.inventory_metric),
            f"Inventory Metrics for {self.inventory_metric.date}"
        )

    def test_customer_metric_str(self):
        """Test the string representation of CustomerMetric"""
        self.assertEqual(
            str(self.customer_metric),
            f"Customer Metrics for {self.customer_metric.date}"
        )

    def test_product_performance_str(self):
        """Test the string representation of ProductPerformance"""
        self.assertEqual(
            str(self.product_performance),
            f"Performance Metrics for {self.product.name} on {self.product_performance.date}"
        )

class AnalyticsAPITests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_superuser(
            email='admin@example.com',
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
            price=Decimal('99.99'),
            category=self.category
        )
        
        # Create test metrics
        self.sales_metric = SalesMetric.objects.create(
            date=timezone.now().date(),
            total_sales=Decimal('999.99'),
            order_count=10,
            average_order_value=Decimal('99.99')
        )

    def test_get_sales_metrics(self):
        """Test retrieving sales metrics"""
        url = reverse('analytics:analytics-sales')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(
            Decimal(response.data[0]['total_sales']),
            self.sales_metric.total_sales
        )

    def test_get_analytics_summary(self):
        """Test retrieving analytics summary"""
        url = reverse('analytics:analytics-summary')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('total_revenue', response.data)
        self.assertIn('total_orders', response.data)
        self.assertIn('average_order_value', response.data)

    def test_generate_report(self):
        """Test generating analytics report"""
        url = reverse('analytics:analytics-generate-report')
        data = {
            'start_date': (timezone.now() - timedelta(days=7)).date().isoformat(),
            'end_date': timezone.now().date().isoformat()
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('sales', response.data)
        self.assertIn('inventory', response.data)
        self.assertIn('customers', response.data)
        self.assertIn('products', response.data)

class AnalyticsAdminTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_superuser(
            email='admin@example.com',
            password='testpass123'
        )
        self.client.force_login(self.user)
        
        self.category = Category.objects.create(
            name='Test Category',
            slug='test-category'
        )
        self.product = Product.objects.create(
            name='Test Product',
            slug='test-product',
            description='Test Description',
            price=Decimal('99.99'),
            category=self.category
        )
        
        # Create test metrics
        self.sales_metric = SalesMetric.objects.create(
            date=timezone.now().date(),
            total_sales=Decimal('999.99'),
            order_count=10,
            average_order_value=Decimal('99.99')
        )

    def test_sales_metric_admin(self):
        """Test sales metric admin list view"""
        url = reverse('admin:analytics_salesmetric_changelist')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'USh 1,000')
        self.assertContains(response, '10')  # order_count

    def test_inventory_metric_admin(self):
        """Test inventory metric admin list view"""
        metric = InventoryMetric.objects.create(
            date=timezone.now().date(),
            metrics_data={
                str(self.product.id): {
                    'product_name': self.product.name,
                    'opening_stock': 100,
                    'current_stock': 90,
                    'units_sold': 10
                }
            }
        )
        url = reverse('admin:analytics_inventorymetric_changelist')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '1 products tracked')

    def test_customer_metric_admin(self):
        """Test customer metric admin list view"""
        metric = CustomerMetric.objects.create(
            date=timezone.now().date(),
            total_customers=100,
            new_customers=20,
            returning_customers=80
        )
        url = reverse('admin:analytics_customermetric_changelist')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '100')  # total_customers
        self.assertContains(response, '20')  # new_customers
