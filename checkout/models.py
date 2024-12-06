from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from decimal import Decimal

class Order(models.Model):
    """Model for orders"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    DELIVERY_CHOICES = [
        ('delivery', 'Delivery'),
        ('pickup', 'Pickup'),
    ]
    
    PAYMENT_METHOD_CHOICES = [
        ('card', 'Credit Card'),
        ('mobile', 'Mobile Money'),
        ('cash', 'Cash on Delivery'),
    ]
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='checkout_orders'
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    delivery_method = models.CharField(max_length=20, choices=DELIVERY_CHOICES)
    delivery_zone = models.ForeignKey(
        'DeliveryZone',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='orders'
    )
    pickup_location = models.ForeignKey(
        'PickupLocation',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='orders'
    )
    payment_method = models.ForeignKey(
        'PaymentMethod',
        on_delete=models.SET_NULL,
        null=True,
        related_name='orders'
    )
    pickup_time = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Order {self.id} - {self.user.email}"

class DeliveryZone(models.Model):
    """Model for defining delivery zones and their fees"""
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    delivery_fee = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    estimated_days = models.PositiveIntegerField(help_text="Estimated delivery days")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class PickupLocation(models.Model):
    """Model for defining pickup locations"""
    name = models.CharField(max_length=100)
    address = models.TextField()
    contact_phone = models.CharField(max_length=20)
    operating_hours = models.TextField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class PaymentMethod(models.Model):
    """Model for payment methods"""
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    provider = models.CharField(max_length=50)
    icon = models.ImageField(upload_to='payment_icons/', null=True, blank=True)
    is_active = models.BooleanField(default=True)
    requires_verification = models.BooleanField(default=False)
    min_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    max_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        default=Decimal('9999999.99')
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class CheckoutSession(models.Model):
    """Model for managing checkout sessions"""
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('PAYMENT_PENDING', 'Payment Pending'),
        ('COMPLETED', 'Completed'),
        ('EXPIRED', 'Expired'),
        ('CANCELLED', 'Cancelled'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    cart = models.OneToOneField('cart.Cart', on_delete=models.CASCADE)
    delivery_type = models.CharField(
        max_length=20,
        choices=[('DELIVERY', 'Delivery'), ('PICKUP', 'Pickup')]
    )
    delivery_zone = models.ForeignKey(
        DeliveryZone,
        null=True,
        blank=True,
        on_delete=models.SET_NULL
    )
    pickup_location = models.ForeignKey(
        PickupLocation,
        null=True,
        blank=True,
        on_delete=models.SET_NULL
    )
    delivery_address = models.TextField(blank=True)
    delivery_instructions = models.TextField(blank=True)
    payment_method = models.ForeignKey(
        PaymentMethod,
        null=True,
        blank=True,
        on_delete=models.SET_NULL
    )
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    delivery_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='PENDING'
    )
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Checkout session for {self.user.email}"

    def calculate_total(self):
        """Calculate total including delivery fee"""
        self.total = self.subtotal + self.delivery_fee
        self.save()
