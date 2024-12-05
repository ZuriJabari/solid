from django.contrib import admin
from .models import Order, OrderItem, OrderStatusHistory, OrderNote, DeliveryZone

@admin.register(DeliveryZone)
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

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = [
        'order_number', 'user', 'status', 'payment_status',
        'delivery_method', 'total', 'created_at'
    ]
    list_filter = [
        'status', 'payment_status', 'delivery_method',
        'created_at', 'delivery_zone'
    ]
    search_fields = [
        'order_number', 'user__email',
        'user__first_name', 'user__last_name',
        'delivery_address'
    ]
    readonly_fields = [
        'order_number', 'subtotal', 'total',
        'created_at', 'updated_at', 'paid_at',
        'processed_at', 'completed_at', 'cancelled_at'
    ]
    inlines = [OrderItemInline, OrderStatusHistoryInline, OrderNoteInline]
    fieldsets = (
        ('Basic Information', {
            'fields': (
                'order_number', 'user', 'status',
                'payment_status'
            )
        }),
        ('Delivery Information', {
            'fields': (
                'delivery_method', 'delivery_zone',
                'delivery_address', 'delivery_instructions',
                'preferred_delivery_date', 'preferred_delivery_time'
            )
        }),
        ('Pickup Information', {
            'fields': (
                'pickup_location', 'pickup_date',
                'pickup_time'
            )
        }),
        ('Amounts', {
            'fields': (
                'subtotal', 'delivery_fee',
                'tax', 'total'
            )
        }),
        ('Tracking', {
            'fields': (
                'tracking_number',
                'estimated_delivery',
                'actual_delivery'
            )
        }),
        ('Timestamps', {
            'fields': (
                'created_at', 'updated_at',
                'paid_at', 'processed_at',
                'completed_at', 'cancelled_at'
            )
        }),
    )

    def save_formset(self, request, form, formset, change):
        instances = formset.save(commit=False)
        for instance in instances:
            if isinstance(instance, (OrderStatusHistory, OrderNote)):
                if not instance.created_by:
                    instance.created_by = request.user
            instance.save()
        formset.save_m2m()

@admin.register(OrderNote)
class OrderNoteAdmin(admin.ModelAdmin):
    list_display = ['order', 'created_by', 'is_public', 'created_at']
    list_filter = ['is_public', 'created_at']
    search_fields = ['order__order_number', 'note']
    readonly_fields = ['created_at', 'created_by']

    def save_model(self, request, obj, form, change):
        if not obj.created_by:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
