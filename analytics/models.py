from django.db import models
from django.conf import settings
from django.utils import timezone
from products.models import Product
from orders.models import Order
from config.currency import format_currency

class SalesMetric(models.Model):
    """Model for tracking sales metrics over time"""
    date = models.DateField(default=timezone.now)
    total_sales = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    order_count = models.PositiveIntegerField(default=0)
    average_order_value = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    refund_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    refund_count = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['-date']
        indexes = [models.Index(fields=['date'])]

    def __str__(self):
        return f"Sales Metrics for {self.date}"

    @property
    def formatted_total_sales(self):
        return format_currency(self.total_sales)

    @property
    def formatted_average_order_value(self):
        return format_currency(self.average_order_value)

    @property
    def formatted_refund_amount(self):
        return format_currency(self.refund_amount)

class InventoryMetric(models.Model):
    """Model for tracking inventory movements and stock levels"""
    date = models.DateField(default=timezone.now)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    opening_stock = models.PositiveIntegerField()
    closing_stock = models.PositiveIntegerField()
    units_sold = models.PositiveIntegerField(default=0)
    units_refunded = models.PositiveIntegerField(default=0)
    restock_amount = models.PositiveIntegerField(default=0)
    low_stock_alerts = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['-date', 'product']
        indexes = [
            models.Index(fields=['date', 'product']),
            models.Index(fields=['product', 'date'])
        ]

    def __str__(self):
        return f"Inventory Metrics for {self.product.name} on {self.date}"

class CustomerMetric(models.Model):
    """Model for tracking customer behavior and engagement"""
    date = models.DateField(default=timezone.now)
    total_customers = models.PositiveIntegerField(default=0)
    new_customers = models.PositiveIntegerField(default=0)
    returning_customers = models.PositiveIntegerField(default=0)
    average_session_duration = models.DurationField(null=True, blank=True)
    cart_abandonment_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    
    class Meta:
        ordering = ['-date']
        indexes = [models.Index(fields=['date'])]

    def __str__(self):
        return f"Customer Metrics for {self.date}"

class ProductPerformance(models.Model):
    """Model for tracking individual product performance"""
    date = models.DateField(default=timezone.now)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    views = models.PositiveIntegerField(default=0)
    add_to_cart_count = models.PositiveIntegerField(default=0)
    purchase_count = models.PositiveIntegerField(default=0)
    revenue = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    conversion_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)

    class Meta:
        ordering = ['-date', '-revenue']
        indexes = [
            models.Index(fields=['date', 'product']),
            models.Index(fields=['product', 'date'])
        ]

    def __str__(self):
        return f"Performance Metrics for {self.product.name} on {self.date}"

    @property
    def formatted_revenue(self):
        return format_currency(self.revenue)
