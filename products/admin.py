from django.contrib import admin
from mptt.admin import MPTTModelAdmin
from .models import (
    Category, Product, ProductImage, ProductReview,
    ReviewVote, ProductInventory, InventoryBatch,
    StockAdjustment
)
from django.db.models import Avg, Count, Q, Sum
from django.utils import timezone
from django.utils.html import format_html

@admin.register(Category)
class CategoryAdmin(MPTTModelAdmin):
    list_display = ['name', 'slug', 'order', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name']
    prepopulated_fields = {'slug': ('name',)}

class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1

class ReviewVoteInline(admin.TabularInline):
    model = ReviewVote
    extra = 0
    readonly_fields = ['user', 'vote', 'created_at']
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False

@admin.register(ProductReview)
class ProductReviewAdmin(admin.ModelAdmin):
    list_display = [
        'product', 'user', 'rating', 'status',
        'is_verified_purchase', 'helpful_votes',
        'created_at'
    ]
    list_filter = [
        'status', 'rating', 'is_verified_purchase',
        'created_at', 'moderated_at'
    ]
    search_fields = [
        'product__name', 'user__email',
        'user__first_name', 'user__last_name',
        'title', 'comment'
    ]
    readonly_fields = [
        'product', 'user', 'helpful_votes',
        'unhelpful_votes', 'created_at', 'updated_at'
    ]
    fieldsets = (
        ('Review', {
            'fields': (
                'product', 'user', 'rating', 'title',
                'comment', 'status', 'is_verified_purchase'
            )
        }),
        ('Moderation', {
            'fields': (
                'moderation_notes', 'moderated_by',
                'moderated_at'
            )
        }),
        ('Statistics', {
            'fields': (
                'helpful_votes', 'unhelpful_votes',
                'created_at', 'updated_at'
            )
        }),
    )
    inlines = [ReviewVoteInline]

    def save_model(self, request, obj, form, change):
        if change and 'status' in form.changed_data:
            obj.moderated_by = request.user
            obj.moderated_at = timezone.now()
        super().save_model(request, obj, form, change)

class InventoryBatchInline(admin.TabularInline):
    model = InventoryBatch
    extra = 1
    fields = [
        'batch_number', 'quantity', 'cost_per_unit',
        'manufacturing_date', 'expiry_date', 'supplier'
    ]

class StockAdjustmentInline(admin.TabularInline):
    model = StockAdjustment
    extra = 0
    fields = [
        'adjustment_type', 'quantity', 'reason',
        'reference_number', 'batch', 'created_at'
    ]
    readonly_fields = ['created_at']
    ordering = ['-created_at']
    max_num = 10  # Limit the number of adjustments shown

@admin.register(ProductInventory)
class ProductInventoryAdmin(admin.ModelAdmin):
    list_display = [
        'product', 'current_stock', 'reorder_point',
        'stock_status', 'last_restock_date', 'batch_count',
        'expiring_soon'
    ]
    list_filter = ['last_restock_date']
    search_fields = ['product__name']
    inlines = [InventoryBatchInline, StockAdjustmentInline]
    readonly_fields = ['current_stock', 'last_restock_date']

    def stock_status(self, obj):
        if obj.current_stock <= 0:
            return format_html(
                '<span style="color: red; font-weight: bold;">Out of Stock</span>'
            )
        elif obj.current_stock <= obj.reorder_point:
            return format_html(
                '<span style="color: orange; font-weight: bold;">Low Stock</span>'
            )
        return format_html(
            '<span style="color: green;">In Stock</span>'
        )
    stock_status.short_description = 'Status'

    def batch_count(self, obj):
        return obj.batches.count()
    batch_count.short_description = 'Batches'

    def expiring_soon(self, obj):
        thirty_days_later = timezone.now().date() + timezone.timedelta(days=30)
        count = obj.batches.filter(
            expiry_date__lte=thirty_days_later,
            quantity__gt=0
        ).count()
        if count > 0:
            return format_html(
                '<span style="color: red;">{} batches</span>',
                count
            )
        return '-'
    expiring_soon.short_description = 'Expiring Soon'

@admin.register(InventoryBatch)
class InventoryBatchAdmin(admin.ModelAdmin):
    list_display = [
        'batch_number', 'inventory', 'quantity',
        'cost_per_unit', 'manufacturing_date',
        'expiry_date', 'supplier'
    ]
    list_filter = ['supplier', 'manufacturing_date', 'expiry_date']
    search_fields = [
        'batch_number', 'inventory__product__name',
        'supplier'
    ]
    date_hierarchy = 'expiry_date'

@admin.register(StockAdjustment)
class StockAdjustmentAdmin(admin.ModelAdmin):
    list_display = [
        'inventory', 'adjustment_type', 'quantity',
        'batch', 'adjusted_by', 'created_at'
    ]
    list_filter = ['adjustment_type', 'created_at', 'adjusted_by']
    search_fields = [
        'inventory__product__name', 'reason',
        'reference_number'
    ]
    readonly_fields = ['adjusted_by', 'created_at']
    date_hierarchy = 'created_at'

    def save_model(self, request, obj, form, change):
        if not obj.adjusted_by:
            obj.adjusted_by = request.user
        super().save_model(request, obj, form, change)

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'category', 'price', 'inventory_status',
        'is_active', 'average_rating', 'review_count',
        'created_at'
    ]
    list_filter = [
        'category', 'is_active', 'potency',
        'inventory__current_stock'
    ]
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ['price', 'is_active']
    inlines = [ProductImageInline]

    def inventory_status(self, obj):
        try:
            inventory = obj.inventory
            if inventory.current_stock <= 0:
                return format_html(
                    '<span style="color: red; font-weight: bold;">'
                    'Out of Stock (0)</span>'
                )
            elif inventory.current_stock <= inventory.reorder_point:
                return format_html(
                    '<span style="color: orange; font-weight: bold;">'
                    'Low Stock ({})</span>', inventory.current_stock
                )
            return format_html(
                '<span style="color: green;">In Stock ({})</span>',
                inventory.current_stock
            )
        except ProductInventory.DoesNotExist:
            return format_html(
                '<span style="color: gray;">No Inventory</span>'
            )
    inventory_status.short_description = 'Stock Status'

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            average_rating=Avg('reviews__rating', filter=Q(reviews__status='approved')),
            review_count=Count('reviews', filter=Q(reviews__status='approved'))
        )

    def average_rating(self, obj):
        return round(obj.average_rating, 1) if obj.average_rating else None
    average_rating.admin_order_field = 'average_rating'

    def review_count(self, obj):
        return obj.review_count
    review_count.admin_order_field = 'review_count'
