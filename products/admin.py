from django.contrib import admin
from mptt.admin import MPTTModelAdmin
from .models import Category, Product, ProductImage, ProductReview, Inventory, StockMovement
from config.admin import SecureModelAdmin, secure_admin_site

class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1

class SecureProductAdmin(SecureModelAdmin):
    list_display = ('name', 'category', 'price', 'is_active', 'created_at')
    list_filter = ('category', 'is_active', 'created_at')
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}
    inlines = [ProductImageInline]
    readonly_fields = ('created_at', 'updated_at')

class SecureCategoryAdmin(MPTTModelAdmin, SecureModelAdmin):
    list_display = ('name', 'parent', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ('created_at', 'updated_at')

class SecureProductReviewAdmin(SecureModelAdmin):
    list_display = ('product', 'user', 'rating', 'is_approved', 'created_at')
    list_filter = ('rating', 'is_approved', 'created_at')
    search_fields = ('product__name', 'user__email', 'comment')
    readonly_fields = ('created_at',)

class StockMovementInline(admin.TabularInline):
    model = StockMovement
    extra = 1
    readonly_fields = ('created_at',)

class SecureInventoryAdmin(SecureModelAdmin):
    list_display = ('product', 'quantity', 'low_stock_threshold')
    list_filter = ('low_stock_threshold',)
    search_fields = ('product__name',)
    inlines = [StockMovementInline]
    readonly_fields = ('created_at', 'updated_at')

# Register with both default admin site and secure admin site
admin.site.register(Product, SecureProductAdmin)
admin.site.register(Category, SecureCategoryAdmin)
admin.site.register(ProductReview, SecureProductReviewAdmin)
admin.site.register(Inventory, SecureInventoryAdmin)

secure_admin_site.register(Product, SecureProductAdmin)
secure_admin_site.register(Category, SecureCategoryAdmin)
secure_admin_site.register(ProductReview, SecureProductReviewAdmin)
secure_admin_site.register(Inventory, SecureInventoryAdmin)
