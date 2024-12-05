from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model
from orders.models import CustomerOrder
import uuid
from django.conf import settings
from django.utils import timezone

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
    PAYMENT_STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('PROCESSING', 'Processing'),
        ('SUCCESSFUL', 'Successful'),
        ('FAILED', 'Failed'),
        ('CANCELLED', 'Cancelled'),
        ('REFUNDED', 'Refunded'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='mobile_payments'
    )
    order = models.ForeignKey(
        CustomerOrder,
        on_delete=models.PROTECT,
        related_name='mobile_payments'
    )
    provider = models.ForeignKey(
        MobilePaymentProvider,
        on_delete=models.PROTECT,
        related_name='payments'
    )
    
    # Payment details
    amount = models.DecimalField(
        _('amount'),
        max_digits=10,
        decimal_places=2
    )
    currency = models.CharField(
        _('currency'),
        max_length=3,
        default='UGX'
    )
    phone_number = models.CharField(_('phone number'), max_length=20)
    
    # Transaction details
    provider_tx_id = models.CharField(
        _('provider transaction ID'),
        max_length=255,
        blank=True
    )
    provider_tx_ref = models.CharField(
        _('provider transaction reference'),
        max_length=255,
        unique=True
    )
    status = models.CharField(
        _('status'),
        max_length=20,
        choices=PAYMENT_STATUS_CHOICES,
        default='PENDING'
    )
    
    # Metadata
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    completed_at = models.DateTimeField(_('completed at'), null=True, blank=True)
    
    class Meta:
        verbose_name = _('mobile payment')
        verbose_name_plural = _('mobile payments')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.provider.name} payment of {self.amount} {self.currency} for order {self.order.id}"

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
