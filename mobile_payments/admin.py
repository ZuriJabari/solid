from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import MobilePaymentProvider, MobilePayment, PaymentNotification

@admin.register(MobilePaymentProvider)
class MobilePaymentProviderAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name', 'code')
    
    fieldsets = (
        (None, {
            'fields': ('name', 'code', 'is_active')
        }),
        (_('API Configuration'), {
            'fields': ('api_base_url', 'api_key', 'api_secret', 'webhook_secret'),
            'classes': ('collapse',)
        }),
    )

@admin.register(MobilePayment)
class MobilePaymentAdmin(admin.ModelAdmin):
    list_display = (
        'provider', 'amount', 'currency', 'status',
        'phone_number', 'created_at', 'completed_at'
    )
    list_filter = ('status', 'provider', 'currency')
    search_fields = (
        'phone_number', 'provider_tx_id',
        'provider_tx_ref', 'user__email'
    )
    readonly_fields = (
        'id', 'created_at', 'updated_at',
        'completed_at', 'provider_tx_id'
    )
    
    fieldsets = (
        (None, {
            'fields': ('id', 'user', 'order', 'provider')
        }),
        (_('Payment Details'), {
            'fields': ('amount', 'currency', 'phone_number')
        }),
        (_('Transaction Details'), {
            'fields': (
                'status', 'provider_tx_id',
                'provider_tx_ref'
            )
        }),
        (_('Timestamps'), {
            'fields': (
                'created_at', 'updated_at',
                'completed_at'
            ),
            'classes': ('collapse',)
        }),
    )

@admin.register(PaymentNotification)
class PaymentNotificationAdmin(admin.ModelAdmin):
    list_display = (
        'notification_type', 'payment', 'provider',
        'status', 'is_processed', 'received_at'
    )
    list_filter = (
        'notification_type', 'status',
        'is_processed', 'provider'
    )
    search_fields = ('payment__provider_tx_ref', 'payment__phone_number')
    readonly_fields = (
        'id', 'received_at', 'processed_at',
        'raw_payload'
    )
    
    fieldsets = (
        (None, {
            'fields': ('id', 'payment', 'provider')
        }),
        (_('Notification Details'), {
            'fields': (
                'notification_type', 'status',
                'raw_payload'
            )
        }),
        (_('Processing Status'), {
            'fields': (
                'is_processed', 'processing_errors',
                'received_at', 'processed_at'
            )
        }),
    )
