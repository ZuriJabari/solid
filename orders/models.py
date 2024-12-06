from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from products.models import Product
import uuid
from decimal import Decimal
from config.currency import MIN_AMOUNT, MAX_AMOUNT, CURRENCY_DECIMAL_PLACES

class DeliveryZone(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    delivery_fee = models.DecimalField(
        max_digits=12,
        decimal_places=CURRENCY_DECIMAL_PLACES,
        validators=[MinValueValidator(Decimal('0'))]
    )
    estimated_days = models.PositiveIntegerField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled')
    ]

    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded')
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    payment_status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS_CHOICES,
        default='pending'
    )
    subtotal = models.DecimalField(
        max_digits=12,
        decimal_places=CURRENCY_DECIMAL_PLACES,
        default=0,
        validators=[MinValueValidator(Decimal('0'))]
    )
    delivery_fee = models.DecimalField(
        max_digits=12,
        decimal_places=CURRENCY_DECIMAL_PLACES,
        default=0,
        validators=[MinValueValidator(Decimal('0'))]
    )
    total = models.DecimalField(
        max_digits=12,
        decimal_places=CURRENCY_DECIMAL_PLACES,
        default=0,
        validators=[MinValueValidator(Decimal('0'))]
    )
    delivery_zone = models.ForeignKey(
        DeliveryZone,
        on_delete=models.PROTECT,
        related_name='orders'
    )
    shipping_address = models.TextField(blank=True)
    tracking_number = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Order {self.id} - {self.user.email}"

    def calculate_subtotal(self):
        return sum(item.subtotal for item in self.items.all())

    def calculate_total(self):
        return self.subtotal + self.delivery_fee

    def save(self, *args, **kwargs):
        if not self.pk:  # Only calculate on creation
            self.delivery_fee = self.delivery_zone.delivery_fee
        super().save(*args, **kwargs)

class OrderItem(models.Model):
    order = models.ForeignKey(
        Order,
        related_name='items',
        on_delete=models.CASCADE
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT
    )
    quantity = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    price = models.DecimalField(
        max_digits=12,
        decimal_places=CURRENCY_DECIMAL_PLACES,
        validators=[MinValueValidator(MIN_AMOUNT)]
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.quantity}x {self.product.name}"

    @property
    def subtotal(self):
        return self.quantity * self.price

    def save(self, *args, **kwargs):
        if not self.pk:  # Only set price on creation
            self.price = self.product.price
        super().save(*args, **kwargs)
        # Update order totals
        self.order.subtotal = self.order.calculate_subtotal()
        self.order.total = self.order.calculate_total()
        self.order.save()

class OrderStatusHistory(models.Model):
    order = models.ForeignKey(
        Order,
        related_name='status_history',
        on_delete=models.CASCADE
    )
    status = models.CharField(max_length=20, choices=Order.STATUS_CHOICES)
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.order.id} - {self.status}"

class OrderNote(models.Model):
    order = models.ForeignKey(
        Order,
        related_name='order_notes',
        on_delete=models.CASCADE
    )
    note = models.TextField()
    is_public = models.BooleanField(default=False)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Note on {self.order.id}"
