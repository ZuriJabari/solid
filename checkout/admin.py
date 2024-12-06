from django.contrib import admin
from django.db import models
from django.db.models import Count, Sum, Avg, Q, F, ExpressionWrapper, FloatField
from django.db.models.functions import TruncDate, TruncMonth, ExtractHour, Now
from django.urls import path
from django.template.response import TemplateResponse
from django.utils.html import format_html, mark_safe
from django.http import HttpResponse, JsonResponse
from django.contrib import messages
from django.utils import timezone
from datetime import datetime, timedelta
from rangefilter.filters import DateRangeFilter
import json
import csv
from .models import Order, DeliveryZone, PickupLocation, PaymentMethod, CheckoutSession
from django.utils.translation import gettext_lazy as _
from config.admin import SecureModelAdmin, secure_admin_site
from config.currency import format_currency

def export_orders_csv(modeladmin, request, queryset):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="orders.csv"'
    
    writer = csv.writer(response)
    writer.writerow([
        'ID', 'User Email', 'Status', 'Total Amount', 'Delivery Method',
        'Payment Method', 'Created At', 'Updated At'
    ])
    
    for order in queryset:
        writer.writerow([
            order.id, order.user.email, order.status, order.total_amount,
            order.delivery_method, order.payment_method, order.created_at,
            order.updated_at
        ])
    
    return response
export_orders_csv.short_description = "Export selected orders to CSV"

def mark_as_completed(modeladmin, request, queryset):
    updated = queryset.filter(status='processing').update(status='completed')
    messages.success(request, f'{updated} orders marked as completed.')
mark_as_completed.short_description = "Mark selected orders as completed"

def mark_as_processing(modeladmin, request, queryset):
    updated = queryset.filter(status='pending').update(status='processing')
    messages.success(request, f'{updated} orders marked as processing.')
mark_as_processing.short_description = "Mark selected orders as processing"

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'user', 'total_amount', 'status', 'delivery_method',
        'payment_status', 'created_at', 'processing_time'
    ]
    list_filter = [
        'status', 'delivery_method', 'payment_method',
        ('created_at', DateRangeFilter),
    ]
    search_fields = ['user__email', 'id']
    date_hierarchy = 'created_at'
    readonly_fields = ['processing_time', 'created_at', 'updated_at']
    actions = [mark_as_completed, mark_as_processing, export_orders_csv]
    change_list_template = 'admin/checkout/order/change_list.html'
    
    fieldsets = (
        ('Order Information', {
            'fields': ('user', 'status', 'total_amount')
        }),
        ('Delivery Details', {
            'fields': ('delivery_method', 'delivery_zone', 'pickup_location')
        }),
        ('Payment Information', {
            'fields': ('payment_method', 'payment_status')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'processing_time'),
            'classes': ('collapse',)
        }),
    )

    def payment_status(self, obj):
        if obj.status == 'completed':
            return format_html('<span style="color: green;">✓ Paid</span>')
        elif obj.status == 'processing':
            return format_html('<span style="color: orange;">⟳ Processing</span>')
        return format_html('<span style="color: red;">✗ Pending</span>')
    payment_status.short_description = 'Payment'

    def processing_time(self, obj):
        if obj.status in ['completed', 'cancelled']:
            time_diff = obj.updated_at - obj.created_at
            minutes = time_diff.total_seconds() / 60
            if minutes < 60:
                return f"{minutes:.1f} minutes"
            return f"{minutes/60:.1f} hours"
        return "In Progress"
    processing_time.short_description = 'Processing Time'

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        qs = qs.select_related('user', 'delivery_zone', 'pickup_location', 'payment_method')
        return qs

    def changelist_view(self, request, extra_context=None):
        response = super().changelist_view(request, extra_context=extra_context)
        
        try:
            qs = self.get_queryset(request)
            
            # Basic metrics
            metrics = {
                'total_orders': qs.count(),
                'total_revenue': qs.aggregate(total=Sum('total_amount'))['total'] or 0,
                'avg_order_value': qs.aggregate(avg=Avg('total_amount'))['avg'] or 0,
                'success_rate': (qs.filter(status='completed').count() / qs.count() * 100) if qs.count() > 0 else 0,
            }
            
            # Performance metrics
            today = timezone.now().date()
            last_week = today - timedelta(days=7)
            
            weekly_metrics = {
                'weekly_orders': qs.filter(created_at__date__gte=last_week).count(),
                'weekly_revenue': qs.filter(created_at__date__gte=last_week).aggregate(
                    total=Sum('total_amount'))['total'] or 0,
                'avg_processing_time': qs.filter(
                    status__in=['completed', 'cancelled'],
                    created_at__date__gte=last_week
                ).annotate(
                    process_time=ExpressionWrapper(
                        F('updated_at') - F('created_at'),
                        output_field=FloatField()
                    )
                ).aggregate(avg=Avg('process_time'))['avg'] or 0,
            }
            
            # Method distribution
            delivery_dist = dict(qs.values_list('delivery_method').annotate(count=Count('id')))
            payment_dist = dict(qs.values_list('payment_method__name').annotate(count=Count('id')))
            
            if not response.context_data:
                response.context_data = {}
            response.context_data.update({
                **metrics,
                **weekly_metrics,
                'delivery_distribution': delivery_dist,
                'payment_distribution': payment_dist,
            })
        except (AttributeError, KeyError):
            pass
        
        return response

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('charts/', self.admin_site.admin_view(self.charts_view), name='checkout_order_charts'),
            path('api/metrics/', self.admin_site.admin_view(self.metrics_api), name='order_metrics_api'),
        ]
        return custom_urls + urls

    def metrics_api(self, request):
        """API endpoint for real-time metrics updates"""
        qs = self.get_queryset(request)
        today = timezone.now().date()
        
        metrics = {
            'today_orders': qs.filter(created_at__date=today).count(),
            'today_revenue': float(qs.filter(created_at__date=today).aggregate(
                total=Sum('total_amount'))['total'] or 0),
            'pending_orders': qs.filter(status='pending').count(),
            'processing_orders': qs.filter(status='processing').count(),
        }
        
        return JsonResponse(metrics)

    def charts_view(self, request):
        """View for displaying charts and analytics"""
        # Get date range (last 30 days)
        end_date = timezone.now()
        start_date = end_date - timedelta(days=30)
        
        # Calculate basic metrics
        qs = self.get_queryset(request)
        total_orders = qs.count()
        total_revenue = qs.aggregate(total=Sum('total_amount'))['total'] or 0
        success_rate = (qs.filter(status='completed').count() / total_orders * 100) if total_orders > 0 else 0
        avg_order_value = qs.aggregate(avg=Avg('total_amount'))['avg'] or 0

        # Daily orders data
        daily_orders = (
            qs.filter(created_at__gte=start_date)
            .annotate(date=TruncDate('created_at'))
            .values('date')
            .annotate(count=Count('id'))
            .order_by('date')
        )
        
        daily_labels = [entry['date'].isoformat() for entry in daily_orders]
        daily_counts = [entry['count'] for entry in daily_orders]

        # Monthly revenue data
        monthly_revenue = (
            qs.filter(status='completed')
            .annotate(month=TruncMonth('created_at'))
            .values('month')
            .annotate(revenue=Sum('total_amount'))
            .order_by('month')
        )
        
        monthly_labels = [entry['month'].strftime('%B %Y') for entry in monthly_revenue]
        monthly_amounts = [float(entry['revenue']) for entry in monthly_revenue]

        # Pickup distribution by hour
        pickup_dist = (
            qs.filter(delivery_method='pickup')
            .annotate(hour=ExtractHour('pickup_time'))
            .values('hour')
            .annotate(count=Count('id'))
            .order_by('hour')
        )
        
        pickup_hours = [entry['hour'] for entry in pickup_dist]
        pickup_counts = [entry['count'] for entry in pickup_dist]

        # Payment methods distribution
        payment_dist = (
            qs.values('payment_method__name')
            .annotate(count=Count('id'))
            .order_by('-count')
        )
        
        payment_methods = [entry['payment_method__name'] for entry in payment_dist]
        payment_counts = [entry['count'] for entry in payment_dist]

        context = {
            **self.admin_site.each_context(request),
            'title': 'Order Analytics',
            'total_orders': total_orders,
            'total_revenue': total_revenue,
            'success_rate': round(success_rate, 1),
            'avg_order_value': avg_order_value,
            'daily_labels': json.dumps(daily_labels),
            'daily_orders': json.dumps(daily_counts),
            'monthly_labels': json.dumps(monthly_labels),
            'monthly_revenue': json.dumps(monthly_amounts),
            'pickup_hours': json.dumps(pickup_hours),
            'pickup_counts': json.dumps(pickup_counts),
            'payment_methods': json.dumps(payment_methods),
            'payment_counts': json.dumps(payment_counts),
        }
        
        return TemplateResponse(request, 'admin/checkout/charts.html', context)

class DeliveryZoneAdmin(SecureModelAdmin):
    list_display = ['name', 'formatted_delivery_fee', 'estimated_days', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name', 'description']

    def formatted_delivery_fee(self, obj):
        return format_currency(obj.delivery_fee)
    formatted_delivery_fee.short_description = _('Delivery Fee')

class PickupLocationAdmin(SecureModelAdmin):
    list_display = ['name', 'address', 'contact_phone', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name', 'address']

class PaymentMethodAdmin(SecureModelAdmin):
    list_display = ['name', 'provider', 'formatted_min_amount', 'formatted_max_amount', 'is_active']
    list_filter = ['provider', 'is_active']
    search_fields = ['name']

    def formatted_min_amount(self, obj):
        return format_currency(obj.min_amount)
    formatted_min_amount.short_description = _('Minimum Amount')

    def formatted_max_amount(self, obj):
        return format_currency(obj.max_amount)
    formatted_max_amount.short_description = _('Maximum Amount')

class CheckoutSessionAdmin(SecureModelAdmin):
    list_display = ['id', 'user', 'status', 'formatted_total', 'created_at']
    list_filter = ['status', 'delivery_type', 'created_at']
    search_fields = ['user__email', 'delivery_address']
    readonly_fields = [
        'formatted_subtotal', 'formatted_delivery_fee', 'formatted_total',
        'created_at', 'expires_at'
    ]

    fieldsets = (
        ('User Info', {
            'fields': ('user', 'status', 'delivery_type')
        }),
        ('Amounts', {
            'fields': ('formatted_subtotal', 'formatted_delivery_fee', 'formatted_total')
        }),
        ('Delivery Details', {
            'fields': ('delivery_zone', 'pickup_location', 'delivery_address', 'delivery_instructions')
        }),
        ('Payment', {
            'fields': ('payment_method',)
        }),
        ('Dates', {
            'fields': ('created_at', 'expires_at')
        }),
    )

    def formatted_subtotal(self, obj):
        return format_currency(obj.subtotal)
    formatted_subtotal.short_description = _('Subtotal')

    def formatted_delivery_fee(self, obj):
        return format_currency(obj.delivery_fee)
    formatted_delivery_fee.short_description = _('Delivery Fee')

    def formatted_total(self, obj):
        return format_currency(obj.total)
    formatted_total.short_description = _('Total')

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(user=request.user)

    def changelist_view(self, request, extra_context=None):
        # Get base queryset
        qs = self.get_queryset(request)
        
        # Calculate statistics
        total_sessions = qs.count()
        completed_sessions = qs.filter(status='COMPLETED').count()
        success_rate = (completed_sessions / total_sessions * 100) if total_sessions > 0 else 0
        
        # Calculate revenue metrics
        total_revenue = qs.filter(status='COMPLETED').aggregate(
            total=Sum('total'))['total'] or 0
        avg_order_value = qs.filter(status='COMPLETED').aggregate(
            avg=Avg('total'))['avg'] or 0

        # Format currency values
        formatted_total_revenue = format_currency(total_revenue)
        formatted_avg_order_value = format_currency(avg_order_value)

        extra_context = extra_context or {}
        extra_context.update({
            'total_sessions': total_sessions,
            'completed_sessions': completed_sessions,
            'success_rate': round(success_rate, 1),
            'total_revenue': formatted_total_revenue,
            'avg_order_value': formatted_avg_order_value,
        })
        
        return super().changelist_view(request, extra_context=extra_context)

# Register with both admin sites
admin.site.register(DeliveryZone, DeliveryZoneAdmin)
admin.site.register(PickupLocation, PickupLocationAdmin)
admin.site.register(PaymentMethod, PaymentMethodAdmin)
admin.site.register(CheckoutSession, CheckoutSessionAdmin)

secure_admin_site.register(DeliveryZone, DeliveryZoneAdmin)
secure_admin_site.register(PickupLocation, PickupLocationAdmin)
secure_admin_site.register(PaymentMethod, PaymentMethodAdmin)
secure_admin_site.register(CheckoutSession, CheckoutSessionAdmin)
