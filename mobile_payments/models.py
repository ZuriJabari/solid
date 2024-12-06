from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model
from orders.models import Order
import uuid
from django.conf import settings
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal
from config.currency import MIN_AMOUNT, MAX_AMOUNT, CURRENCY_DECIMAL_PLACES, CURRENCY

User = get_user_model()

class MobilePaymentProvider(models.Model):
    """Model for mobile money providers (MTN, Airtel)"""
    name = models.CharField(_('provider name'), max_length=50)
    code = models.CharField(_('provider code'), max_length=10, unique=True)
    is_active = models.BooleanField(_('active'), default=True)
    api_base_url = models.URLField(_('API base URL'))
    api_key = models.CharField(_('API key'), max_length=255)
    api_secret = models.CharField(_('API secret'), max_length=255)
    webhook_secret = models.CharField(_('webhook secret'), max_length=255)
    
    class Meta:
        verbose_name = _('mobile payment provider')
        verbose_name_plural = _('mobile payment providers')
    
    def __str__(self):
        return self.name

class MobilePayment(models.Model):
    """Model for mobile money payments"""
    PROVIDER_CHOICES = [
        ('MTN', 'MTN Mobile Money'),
        ('AIRTEL', 'Airtel Money'),
    ]

    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('PROCESSING', 'Processing'),
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed'),
        ('CANCELLED', 'Cancelled'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='mobile_payments'
    )
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='mobile_payments'
    )
    provider = models.CharField(
        max_length=10,
        choices=PROVIDER_CHOICES
    )
    phone_number = models.CharField(max_length=15)
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=CURRENCY_DECIMAL_PLACES,
        validators=[
            MinValueValidator(MIN_AMOUNT),
            MaxValueValidator(MAX_AMOUNT)
        ]
    )
    currency = models.CharField(
        max_length=3,
        default=CURRENCY
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    transaction_id = models.CharField(
        max_length=100,
        unique=True,
        null=True,
        blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['transaction_id']),
            models.Index(fields=['status']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"{self.provider} payment for order {self.order.id}"

    def save(self, *args, **kwargs):
        if self.status == 'SUCCESSFUL' and not self.completed_at:
            self.completed_at = timezone.now()
        super().save(*args, **kwargs)

class PaymentNotification(models.Model):
    """Model for storing payment notifications/webhooks"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    payment = models.ForeignKey(
        MobilePayment,
        on_delete=models.PROTECT,
        related_name='notifications'
    )
    provider = models.ForeignKey(
        MobilePaymentProvider,
        on_delete=models.PROTECT,
        related_name='notifications'
    )
    
    # Notification details
    notification_type = models.CharField(_('notification type'), max_length=50)
    status = models.CharField(_('status'), max_length=50)
    raw_payload = models.JSONField(_('raw payload'))
    
    # Processing status
    is_processed = models.BooleanField(_('processed'), default=False)
    processing_errors = models.TextField(_('processing errors'), blank=True)
    
    # Metadata
    received_at = models.DateTimeField(_('received at'), auto_now_add=True)
    processed_at = models.DateTimeField(_('processed at'), null=True, blank=True)
    
    class Meta:
        verbose_name = _('payment notification')
        verbose_name_plural = _('payment notifications')
        ordering = ['-received_at']
    
    def __str__(self):
        return f"{self.notification_type} notification for payment {self.payment.id}"

    def save(self, *args, **kwargs):
        if self.is_processed and not self.processed_at:
            self.processed_at = timezone.now()
        super().save(*args, **kwargs)
