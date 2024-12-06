from django.contrib import admin
from .models import Order, OrderItem, OrderStatusHistory, OrderNote, DeliveryZone
from config.admin import SecureModelAdmin, secure_admin_site

class DeliveryZoneAdmin(admin.ModelAdmin):
    list_display = ['name', 'delivery_fee', 'estimated_days', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name', 'description']

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ['subtotal']

class OrderStatusHistoryInline(admin.TabularInline):
    model = OrderStatusHistory
    extra = 0
    readonly_fields = ['created_at']
    ordering = ['-created_at']

class OrderNoteInline(admin.TabularInline):
    model = OrderNote
    extra = 0
    readonly_fields = ['created_at', 'created_by']

class SecureOrderAdmin(SecureModelAdmin):
    list_display = ('id', 'user', 'status', 'total', 'created_at')
    list_filter = ('status', 'payment_status', 'created_at')
    search_fields = ('id', 'user__email', 'shipping_address')
    readonly_fields = ('created_at', 'updated_at', 'total')
    inlines = [OrderItemInline, OrderStatusHistoryInline, OrderNoteInline]
    
    fieldsets = (
        ('Order Info', {
            'fields': ('user', 'status', 'payment_status', 'total')
        }),
        ('Shipping', {
            'fields': ('shipping_address', 'tracking_number')
        }),
        ('Dates', {
            'fields': ('created_at', 'updated_at')
        }),
    )

# Register with both admin sites
admin.site.register(Order, SecureOrderAdmin)
secure_admin_site.register(Order, SecureOrderAdmin)

# Register DeliveryZone with both admin sites
admin.site.register(DeliveryZone, DeliveryZoneAdmin)
secure_admin_site.register(DeliveryZone, DeliveryZoneAdmin)

@admin.register(OrderNote)
class OrderNoteAdmin(admin.ModelAdmin):
    list_display = ['order', 'created_by', 'is_public', 'created_at']
    list_filter = ['is_public', 'created_at']
    search_fields = ['order__id', 'note']
    readonly_fields = ['created_at', 'created_by']

    def save_model(self, request, obj, form, change):
        if not obj.created_by:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
