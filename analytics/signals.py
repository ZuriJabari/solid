from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.utils import timezone
from django.db.models import Count, Sum, Avg
from django.contrib.auth import get_user_model
from orders.models import Order
from products.models import Product
from .models import (
    SalesMetric, InventoryMetric,
    CustomerMetric, ProductPerformance
)

User = get_user_model()

@receiver(post_save, sender=Order)
def update_sales_metrics(sender, instance, created, **kwargs):
    """Update sales metrics when an order is created or modified"""
    date = instance.created_at.date()
    
    # Get or create metrics for today
    metrics, _ = SalesMetric.objects.get_or_create(date=date)
    
    # Update total sales and order count
    daily_orders = Order.objects.filter(
        created_at__date=date,
        status='completed'
    )
    
    metrics.total_sales = daily_orders.aggregate(
        total=Sum('total_amount')
    )['total'] or 0
    
    metrics.order_count = daily_orders.count()
    
    if metrics.order_count > 0:
        metrics.average_order_value = metrics.total_sales / metrics.order_count
    else:
        metrics.average_order_value = 0
    
    # Update refund metrics
    refunded_orders = daily_orders.filter(status='refunded')
    metrics.refund_amount = refunded_orders.aggregate(
        total=Sum('total_amount')
    )['total'] or 0
    metrics.refund_count = refunded_orders.count()
    
    metrics.save()

@receiver(post_save, sender=Order)
def update_inventory_metrics(sender, instance, created, **kwargs):
    """Update inventory metrics when an order is created or modified"""
    date = instance.created_at.date()
    
    # Update metrics for each product in the order
    for item in instance.items.all():
        product = item.product
        
        # Get or create metrics for today and this product
        metrics, created = InventoryMetric.objects.get_or_create(
            date=date,
            product=product,
            defaults={
                'opening_stock': product.stock,
                'closing_stock': product.stock
            }
        )
        
        if instance.status == 'completed':
            metrics.units_sold = Order.objects.filter(
                created_at__date=date,
                status='completed',
                items__product=product
            ).aggregate(
                total=Sum('items__quantity')
            )['total'] or 0
        
        if instance.status == 'refunded':
            metrics.units_refunded = Order.objects.filter(
                created_at__date=date,
                status='refunded',
                items__product=product
            ).aggregate(
                total=Sum('items__quantity')
            )['total'] or 0
        
        # Update closing stock
        metrics.closing_stock = product.stock
        
        # Check for low stock
        if product.stock <= product.low_stock_threshold:
            metrics.low_stock_alerts += 1
        
        metrics.save()

@receiver([post_save, post_delete], sender=User)
def update_customer_metrics(sender, instance, **kwargs):
    """Update customer metrics when a user is created or modified"""
    date = timezone.now().date()
    
    # Get or create metrics for today
    metrics, _ = CustomerMetric.objects.get_or_create(date=date)
    
    # Update total customers
    metrics.total_customers = User.objects.count()
    
    # Update new customers (registered today)
    metrics.new_customers = User.objects.filter(
        date_joined__date=date
    ).count()
    
    # Update returning customers (have more than one order)
    returning_customers = User.objects.annotate(
        order_count=Count('order')
    ).filter(order_count__gt=1).count()
    metrics.returning_customers = returning_customers
    
    # Calculate cart abandonment rate
    total_carts = User.objects.filter(cart__isnull=False).count()
    completed_orders = Order.objects.filter(
        status='completed'
    ).values('user').distinct().count()
    
    if total_carts > 0:
        abandonment_rate = ((total_carts - completed_orders) / total_carts) * 100
        metrics.cart_abandonment_rate = round(abandonment_rate, 2)
    
    metrics.save()

@receiver(post_save, sender=Order)
def update_product_performance(sender, instance, created, **kwargs):
    """Update product performance metrics when an order is created or modified"""
    date = instance.created_at.date()
    
    # Update metrics for each product in the order
    for item in instance.items.all():
        product = item.product
        
        # Get or create metrics for today and this product
        metrics, _ = ProductPerformance.objects.get_or_create(
            date=date,
            product=product
        )
        
        if instance.status == 'completed':
            # Update purchase count and revenue
            metrics.purchase_count = Order.objects.filter(
                created_at__date=date,
                status='completed',
                items__product=product
            ).count()
            
            metrics.revenue = Order.objects.filter(
                created_at__date=date,
                status='completed',
                items__product=product
            ).aggregate(
                total=Sum('items__total_price')
            )['total'] or 0
        
        # Calculate conversion rate
        if metrics.views > 0:
            metrics.conversion_rate = (metrics.purchase_count / metrics.views) * 100
        
        metrics.save() 