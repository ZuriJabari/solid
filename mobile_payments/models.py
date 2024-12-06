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
import json

User = get_user_model()

class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return str(obj)
        return super().default(obj)

class MobilePaymentProvider(models.Model):
    """Model for mobile money providers (MTN, Airtel)"""
    PROVIDER_CHOICES = [
        ('MTN', 'MTN Mobile Money'),
        ('AIRTEL', 'Airtel Money'),
    ]
    
    name = models.CharField(_('provider name'), max_length=50)
    code = models.CharField(_('provider code'), max_length=10, choices=PROVIDER_CHOICES, unique=True)
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
    STATUS_CHOICES = [
        ('PENDING', _('Pending')),
        ('PROCESSING', _('Processing')),
        ('SUCCESSFUL', _('Successful')),
        ('FAILED', _('Failed')),
        ('CANCELLED', _('Cancelled')),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.PROTECT, related_name='mobile_payments')
    order = models.ForeignKey(Order, on_delete=models.PROTECT, related_name='mobile_payments')
    provider = models.ForeignKey(MobilePaymentProvider, on_delete=models.PROTECT)
    amount = models.DecimalField(
        max_digits=10, 
        decimal_places=CURRENCY_DECIMAL_PLACES,
        validators=[
            MinValueValidator(MIN_AMOUNT),
            MaxValueValidator(MAX_AMOUNT)
        ]
    )
    phone_number = models.CharField(_('phone number'), max_length=15)
    status = models.CharField(_('status'), max_length=20, choices=STATUS_CHOICES, default='PENDING')
    transaction_id = models.CharField(_('transaction ID'), max_length=100, unique=True, null=True, blank=True)
    provider_reference = models.CharField(_('provider reference'), max_length=100, null=True, blank=True)
    provider_response = models.JSONField(_('provider response'), null=True, blank=True)
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    
    class Meta:
        verbose_name = _('mobile payment')
        verbose_name_plural = _('mobile payments')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.provider.name} - {self.amount} {CURRENCY} - {self.status}"

class PaymentNotification(models.Model):
    """Model for storing payment notifications/webhooks from providers"""
    payment = models.ForeignKey(MobilePayment, on_delete=models.PROTECT, related_name='notifications')
    provider = models.ForeignKey(MobilePaymentProvider, on_delete=models.PROTECT)
    notification_type = models.CharField(_('notification type'), max_length=50)
    payload = models.JSONField(_('notification payload'), default=dict, encoder=DecimalEncoder)
    processed = models.BooleanField(_('processed'), default=False)
    created_at = models.DateTimeField(_('created at'), default=timezone.now)
    
    class Meta:
        verbose_name = _('payment notification')
        verbose_name_plural = _('payment notifications')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.provider.name} - {self.notification_type} - {self.created_at}"
