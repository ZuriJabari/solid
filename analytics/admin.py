from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from rangefilter.filters import DateRangeFilter
from .models import SalesMetric, InventoryMetric, CustomerMetric, ProductPerformance
from config.admin import SecureModelAdmin, secure_admin_site

class SalesMetricAdmin(SecureModelAdmin):
    list_display = ('date', 'formatted_total_sales', 'order_count', 'formatted_average_order_value')
    list_filter = (('date', DateRangeFilter),)
    date_hierarchy = 'date'
    readonly_fields = ('formatted_total_sales', 'formatted_average_order_value', 'formatted_refund_amount')

class InventoryMetricAdmin(SecureModelAdmin):
    list_display = ('date', 'get_metrics_summary')
    list_filter = ('date',)
    search_fields = ('metrics_data',)

    def get_metrics_summary(self, obj):
        return f"{len(obj.metrics_data)} products tracked"
    get_metrics_summary.short_description = 'Metrics Summary'

class CustomerMetricAdmin(SecureModelAdmin):
    list_display = ('date', 'new_customers', 'returning_customers', 'total_customers')
    list_filter = (('date', DateRangeFilter),)
    date_hierarchy = 'date'

class ProductPerformanceAdmin(SecureModelAdmin):
    list_display = ('date', 'product', 'views', 'purchase_count')
    list_filter = ('product__category',)
    search_fields = ('product__name',)
    date_hierarchy = 'date'

# Register with both admin sites for testing
admin.site.register(SalesMetric, SalesMetricAdmin)
admin.site.register(InventoryMetric, InventoryMetricAdmin)
admin.site.register(CustomerMetric, CustomerMetricAdmin)
admin.site.register(ProductPerformance, ProductPerformanceAdmin)

# Register with secure admin site for production
secure_admin_site.register(SalesMetric, SalesMetricAdmin)
secure_admin_site.register(InventoryMetric, InventoryMetricAdmin)
secure_admin_site.register(CustomerMetric, CustomerMetricAdmin)
secure_admin_site.register(ProductPerformance, ProductPerformanceAdmin)
