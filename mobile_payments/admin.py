from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import MobilePaymentProvider, MobilePayment, PaymentNotification
from config.admin import SecureModelAdmin, secure_admin_site

class SecureMobilePaymentProviderAdmin(SecureModelAdmin):
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

class SecureMobilePaymentAdmin(SecureModelAdmin):
    list_display = ('id', 'user', 'amount', 'status', 'provider', 'created_at')
    list_filter = ('status', 'provider', 'created_at')
    search_fields = ('id', 'user__email', 'phone_number')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Payment Info', {
            'fields': ('user', 'amount', 'status', 'provider')
        }),
        ('Contact', {
            'fields': ('phone_number', 'email')
        }),
        ('Transaction Details', {
            'fields': ('provider_reference', 'provider_response')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )

class SecurePaymentNotificationAdmin(SecureModelAdmin):
    list_display = (
        'notification_type', 'payment', 'provider',
        'status', 'is_processed', 'received_at'
    )
    list_filter = (
        'notification_type', 'status',
        'is_processed', 'provider'
    )
    search_fields = ('payment__id', 'payment__phone_number')
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

# Register with both default admin site and secure admin site
admin.site.register(MobilePaymentProvider, SecureMobilePaymentProviderAdmin)
admin.site.register(MobilePayment, SecureMobilePaymentAdmin)
admin.site.register(PaymentNotification, SecurePaymentNotificationAdmin)

secure_admin_site.register(MobilePaymentProvider, SecureMobilePaymentProviderAdmin)
secure_admin_site.register(MobilePayment, SecureMobilePaymentAdmin)
secure_admin_site.register(PaymentNotification, SecurePaymentNotificationAdmin)
