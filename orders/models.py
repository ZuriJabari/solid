from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from django.utils import timezone
from products.models import Product

class DeliveryZone(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    delivery_fee = models.DecimalField(max_digits=10, decimal_places=2)
    estimated_days = models.PositiveIntegerField(help_text="Estimated delivery days")
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

class ShippingAddress(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    full_name = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=20)
    street_address = models.CharField(max_length=255)
    apartment = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20)
    country = models.CharField(max_length=100)
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.full_name} - {self.city}, {self.country}"

    class Meta:
        verbose_name_plural = 'Shipping addresses'

class Order(models.Model):
    DELIVERY_CHOICES = [
        ('delivery', 'Home Delivery'),
        ('pickup', 'Store Pickup'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending Payment'),
        ('paid', 'Payment Received'),
        ('processing', 'Processing'),
        ('ready_for_pickup', 'Ready for Pickup'),
        ('out_for_delivery', 'Out for Delivery'),
        ('delivered', 'Delivered'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('refunded', 'Refunded'),
    ]

    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
        ('partially_refunded', 'Partially Refunded'),
    ]

    # Basic Information
    order_number = models.CharField(max_length=50, unique=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='orders')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
    
    # Delivery Information
    delivery_method = models.CharField(max_length=20, choices=DELIVERY_CHOICES)
    delivery_zone = models.ForeignKey(
        DeliveryZone,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='orders'
    )
    delivery_address = models.TextField(blank=True)
    delivery_instructions = models.TextField(blank=True)
    preferred_delivery_date = models.DateField(null=True, blank=True)
    preferred_delivery_time = models.TimeField(null=True, blank=True)
    
    # Pickup Information
    pickup_location = models.CharField(max_length=255, blank=True)
    pickup_date = models.DateField(null=True, blank=True)
    pickup_time = models.TimeField(null=True, blank=True)
    
    # Amounts
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    delivery_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tax = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    
    # Tracking
    tracking_number = models.CharField(max_length=100, blank=True)
    estimated_delivery = models.DateTimeField(null=True, blank=True)
    actual_delivery = models.DateTimeField(null=True, blank=True)
    shipping_address = models.ForeignKey(ShippingAddress, on_delete=models.PROTECT, null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['order_number']),
        ]

    def __str__(self):
        return f"Order {self.order_number}"

    def save(self, *args, **kwargs):
        if not self.order_number:
            # Generate order number: YYYYMMDD-XXXX
            last_order = Order.objects.order_by('-order_number').first()
            if last_order and last_order.order_number[:8] == timezone.now().strftime('%Y%m%d'):
                count = int(last_order.order_number[-4:]) + 1
            else:
                count = 1
            self.order_number = f"{timezone.now().strftime('%Y%m%d')}-{str(count).zfill(4)}"

        # Update timestamps based on status changes
        if self.status == 'paid' and not self.paid_at:
            self.paid_at = timezone.now()
        elif self.status == 'processing' and not self.processed_at:
            self.processed_at = timezone.now()
        elif self.status == 'completed' and not self.completed_at:
            self.completed_at = timezone.now()
        elif self.status == 'cancelled' and not self.cancelled_at:
            self.cancelled_at = timezone.now()

        super().save(*args, **kwargs)

class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    
    def save(self, *args, **kwargs):
        self.subtotal = self.quantity * self.unit_price
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.quantity}x {self.product.name}"

class OrderStatusHistory(models.Model):
    order = models.ForeignKey(Order, related_name='status_history', on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=Order.STATUS_CHOICES)
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='order_status_updates'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = 'Order status histories'

    def __str__(self):
        return f"{self.order.order_number} - {self.status}"

class OrderNote(models.Model):
    order = models.ForeignKey(Order, related_name='notes', on_delete=models.CASCADE)
    note = models.TextField()
    is_public = models.BooleanField(default=False, help_text="If True, customer can see this note")
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Note on {self.order.order_number}"
