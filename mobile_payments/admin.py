from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.urls import path
from django.template.response import TemplateResponse
from django.db.models import Count, Sum, Avg, F, ExpressionWrapper, FloatField
from django.db.models.functions import ExtractHour
from django.utils import timezone
from datetime import timedelta
import json
from .models import MobilePaymentProvider, MobilePayment, PaymentNotification
from config.admin import SecureModelAdmin, secure_admin_site
from django.db.models import Q

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
        (_('Payment Info'), {
            'fields': ('user', 'order', 'amount', 'status', 'provider')
        }),
        (_('Contact'), {
            'fields': ('phone_number',)
        }),
        (_('Transaction Details'), {
            'fields': ('transaction_id', 'provider_reference', 'provider_response')
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                'dashboard/',
                self.admin_site.admin_view(self.dashboard_view),
                name='mobile_payments_dashboard'
            ),
        ]
        return custom_urls + urls
    
    def dashboard_view(self, request):
        # Get today's and yesterday's dates
        today = timezone.now().date()
        yesterday = today - timedelta(days=1)
        
        # Calculate today's stats
        today_stats = MobilePayment.objects.filter(
            created_at__date=today
        ).aggregate(
            total=Count('id'),
            amount=Sum('amount')
        )
        
        # Calculate yesterday's stats for comparison
        yesterday_stats = MobilePayment.objects.filter(
            created_at__date=yesterday
        ).aggregate(
            total=Count('id'),
            amount=Sum('amount')
        )
        
        # Calculate success rate
        success_stats = MobilePayment.objects.filter(
            created_at__date=today
        ).aggregate(
            total=Count('id'),
            successful=Count('id', filter=Q(status='SUCCESSFUL'))
        )
        
        yesterday_success_stats = MobilePayment.objects.filter(
            created_at__date=yesterday
        ).aggregate(
            total=Count('id'),
            successful=Count('id', filter=Q(status='SUCCESSFUL'))
        )
        
        # Calculate average processing time
        processing_time = MobilePayment.objects.filter(
            status='SUCCESSFUL'
        ).aggregate(
            avg_time=Avg(
                ExpressionWrapper(
                    F('updated_at') - F('created_at'),
                    output_field=FloatField()
                ) * 24 * 60  # Convert to minutes
            )
        )
        
        # Calculate trends
        total_trend = (
            ((today_stats['total'] or 0) - (yesterday_stats['total'] or 0)) /
            (yesterday_stats['total'] or 1)
        ) * 100
        
        amount_trend = (
            ((today_stats['amount'] or 0) - (yesterday_stats['amount'] or 0)) /
            (yesterday_stats['amount'] or 1)
        ) * 100
        
        success_rate = (
            (success_stats['successful'] or 0) /
            (success_stats['total'] or 1)
        ) * 100
        
        yesterday_success_rate = (
            (yesterday_success_stats['successful'] or 0) /
            (yesterday_success_stats['total'] or 1)
        ) * 100
        
        success_trend = success_rate - yesterday_success_rate
        
        # Prepare stats for template
        stats = {
            'total_today': today_stats['total'] or 0,
            'total_trend': round(total_trend, 1),
            'amount_today': today_stats['amount'] or 0,
            'amount_trend': round(amount_trend, 1),
            'success_rate': round(success_rate, 1),
            'success_trend': round(success_trend, 1),
            'avg_processing_time': round(processing_time['avg_time'] or 0, 1)
        }
        
        # Prepare volume data (last 7 days)
        last_7_days = []
        volume_values = []
        for i in range(6, -1, -1):
            date = today - timedelta(days=i)
            count = MobilePayment.objects.filter(created_at__date=date).count()
            last_7_days.append(date.strftime('%Y-%m-%d'))
            volume_values.append(count)
        
        # Prepare status distribution data
        status_data = MobilePayment.objects.values('status').annotate(
            count=Count('id')
        ).order_by('status')
        
        # Prepare provider distribution data
        provider_data = MobilePayment.objects.values(
            'provider__name'
        ).annotate(
            count=Count('id')
        ).order_by('provider__name')
        
        # Prepare hourly distribution data
        hourly_data = MobilePayment.objects.annotate(
            hour=ExtractHour('created_at')
        ).values('hour').annotate(
            count=Count('id')
        ).order_by('hour')
        
        # Get recent payments
        recent_payments = MobilePayment.objects.select_related(
            'user', 'provider'
        ).order_by('-created_at')[:10]
        
        context = {
            **self.admin_site.each_context(request),
            'title': _('Payment Processing Dashboard'),
            'stats': stats,
            'volume_data': {
                'labels': json.dumps(last_7_days),
                'values': json.dumps(volume_values)
            },
            'status_data': {
                'labels': json.dumps([x['status'] for x in status_data]),
                'values': json.dumps([x['count'] for x in status_data])
            },
            'provider_data': {
                'labels': json.dumps([x['provider__name'] for x in provider_data]),
                'values': json.dumps([x['count'] for x in provider_data])
            },
            'hourly_data': {
                'labels': json.dumps([str(x['hour']) for x in hourly_data]),
                'values': json.dumps([x['count'] for x in hourly_data])
            },
            'recent_payments': recent_payments
        }
        
        return TemplateResponse(
            request,
            'admin/mobile_payments/dashboard.html',
            context
        )

class SecurePaymentNotificationAdmin(SecureModelAdmin):
    list_display = ('id', 'payment', 'provider', 'notification_type', 'processed', 'created_at')
    list_filter = ('provider', 'notification_type', 'processed', 'created_at')
    search_fields = ('payment__id', 'provider__name')
    readonly_fields = ('created_at',)
    
    fieldsets = (
        (_('Notification Info'), {
            'fields': ('payment', 'provider', 'notification_type')
        }),
        (_('Processing'), {
            'fields': ('processed', 'payload')
        }),
        (_('Timestamps'), {
            'fields': ('created_at',)
        }),
    )

secure_admin_site.register(MobilePaymentProvider, SecureMobilePaymentProviderAdmin)
secure_admin_site.register(MobilePayment, SecureMobilePaymentAdmin)
secure_admin_site.register(PaymentNotification, SecurePaymentNotificationAdmin)
