from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import SalesMetric, InventoryMetric, CustomerMetric, ProductPerformance
from config.admin import SecureModelAdmin, secure_admin_site

class SalesMetricAdmin(SecureModelAdmin):
    list_display = (
        'date', 'formatted_total_sales', 'order_count',
        'formatted_average_order_value', 'refund_count'
    )
    list_filter = ('date',)
    date_hierarchy = 'date'
    readonly_fields = (
        'formatted_total_sales',
        'formatted_average_order_value'
    )

    fieldsets = (
        (None, {
            'fields': ('date',)
        }),
        (_('Sales Information'), {
            'fields': (
                'total_sales', 'formatted_total_sales',
                'order_count', 'average_order_value',
                'formatted_average_order_value'
            )
        }),
        (_('Refunds'), {
            'fields': ('refund_amount', 'refund_count')
        })
    )

class InventoryMetricAdmin(SecureModelAdmin):
    list_display = (
        'date', 'product', 'opening_stock',
        'closing_stock', 'units_sold', 'low_stock_alerts'
    )
    list_filter = ('date', 'product', 'low_stock_alerts')
    date_hierarchy = 'date'
    search_fields = ('product__name',)

    fieldsets = (
        (None, {
            'fields': ('date', 'product')
        }),
        (_('Stock Levels'), {
            'fields': ('opening_stock', 'closing_stock')
        }),
        (_('Movement'), {
            'fields': (
                'units_sold', 'units_refunded',
                'restock_amount', 'low_stock_alerts'
            )
        })
    )

class CustomerMetricAdmin(SecureModelAdmin):
    list_display = (
        'date', 'total_customers', 'new_customers',
        'returning_customers', 'cart_abandonment_rate'
    )
    list_filter = ('date',)
    date_hierarchy = 'date'

    fieldsets = (
        (None, {
            'fields': ('date',)
        }),
        (_('Customer Counts'), {
            'fields': (
                'total_customers', 'new_customers',
                'returning_customers'
            )
        }),
        (_('Behavior'), {
            'fields': (
                'average_session_duration',
                'cart_abandonment_rate'
            )
        })
    )

class ProductPerformanceAdmin(SecureModelAdmin):
    list_display = (
        'date', 'product', 'views',
        'purchase_count', 'formatted_revenue',
        'conversion_rate'
    )
    list_filter = ('date', 'product')
    date_hierarchy = 'date'
    search_fields = ('product__name',)
    readonly_fields = ('formatted_revenue',)

    fieldsets = (
        (None, {
            'fields': ('date', 'product')
        }),
        (_('Performance Metrics'), {
            'fields': (
                'views', 'add_to_cart_count',
                'purchase_count', 'revenue',
                'formatted_revenue', 'conversion_rate'
            )
        })
    )

# Register with both admin sites
admin.site.register(SalesMetric, SalesMetricAdmin)
admin.site.register(InventoryMetric, InventoryMetricAdmin)
admin.site.register(CustomerMetric, CustomerMetricAdmin)
admin.site.register(ProductPerformance, ProductPerformanceAdmin)

secure_admin_site.register(SalesMetric, SalesMetricAdmin)
secure_admin_site.register(InventoryMetric, InventoryMetricAdmin)
secure_admin_site.register(CustomerMetric, CustomerMetricAdmin)
secure_admin_site.register(ProductPerformance, ProductPerformanceAdmin)
