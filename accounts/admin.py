from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from django.urls import reverse
from .models import User, Address, UserPreference
from config.admin import SecureModelAdmin, secure_admin_site

class AddressInline(admin.StackedInline):
    model = Address
    extra = 0
    classes = ['collapse']
    fieldsets = (
        ('Contact Information', {
            'fields': ('full_name', 'phone')
        }),
        ('Address Details', {
            'fields': ('address_type', 'street_address1', 'street_address2', 
                      'city', 'state', 'postal_code', 'country')
        }),
        ('Settings', {
            'fields': ('is_default',)
        }),
    )

class UserPreferenceInline(admin.StackedInline):
    model = UserPreference
    can_delete = False
    classes = ['collapse']
    filter_horizontal = ('preferred_categories', 'wishlist_items', 'saved_items')
    readonly_fields = ('created_at', 'updated_at', 'wishlist_count', 'saved_items_count')
    
    def wishlist_count(self, obj):
        count = obj.wishlist_items.count()
        if count > 0:
            url = reverse('admin:products_product_changelist') + f'?id__in={",".join(str(id) for id in obj.wishlist_items.values_list("id", flat=True))}'
            return format_html('<a href="{}">{} items</a>', url, count)
        return '0 items'
    wishlist_count.short_description = 'Wishlist'

    def saved_items_count(self, obj):
        count = obj.saved_items.count()
        if count > 0:
            url = reverse('admin:products_product_changelist') + f'?id__in={",".join(str(id) for id in obj.saved_items.values_list("id", flat=True))}'
            return format_html('<a href="{}">{} items</a>', url, count)
        return '0 items'
    saved_items_count.short_description = 'Saved Items'

    fieldsets = (
        ('Display & Notifications', {
            'fields': (
                'theme',
                ('email_notifications', 'push_notifications'),
            ),
            'classes': ('wide',)
        }),
        ('Shopping Preferences', {
            'fields': (
                ('default_shipping_address', 'default_billing_address'),
                'preferred_categories',
            ),
            'classes': ('wide',)
        }),
        ('Saved Products', {
            'fields': (
                ('wishlist_count', 'saved_items_count'),
                'wishlist_items',
                'saved_items',
            ),
            'classes': ('wide',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

class SecureUserAdmin(UserAdmin, SecureModelAdmin):
    list_display = ('email', 'full_name', 'phone', 'is_active', 'is_staff', 'date_joined', 'last_login')
    list_filter = ('is_active', 'is_staff', 'groups', 'date_joined', 'last_login')
    search_fields = ('email', 'first_name', 'last_name', 'phone')
    ordering = ('-date_joined',)
    inlines = [UserPreferenceInline, AddressInline]
    
    def full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}"
    full_name.admin_order_field = 'first_name'
    
    fieldsets = (
        ('Account Information', {
            'fields': ('email', 'password'),
            'classes': ('wide',)
        }),
        ('Personal Information', {
            'fields': (
                ('first_name', 'last_name'),
                'phone',
                'date_of_birth'
            ),
            'classes': ('wide',)
        }),
        ('Email Settings', {
            'fields': (
                'email_verified',
                'newsletter_subscribed',
                'marketing_preferences'
            ),
            'classes': ('collapse',)
        }),
        ('Permissions', {
            'fields': (
                'is_active',
                'is_staff',
                'is_superuser',
                'groups',
                'user_permissions'
            ),
            'classes': ('collapse',)
        }),
        ('Important Dates', {
            'fields': ('last_login', 'date_joined'),
            'classes': ('collapse',)
        }),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'email',
                ('first_name', 'last_name'),
                ('password1', 'password2')
            ),
        }),
    )

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        is_superuser = request.user.is_superuser
        
        if not is_superuser:
            if 'is_superuser' in form.base_fields:
                form.base_fields['is_superuser'].disabled = True
            if 'user_permissions' in form.base_fields:
                form.base_fields['user_permissions'].disabled = True
        return form

class AddressAdmin(SecureModelAdmin):
    list_display = ('user_email', 'full_name', 'address_type', 'city', 'state', 'is_default')
    list_filter = ('address_type', 'is_default', 'state', 'country')
    search_fields = ('user__email', 'full_name', 'city', 'state', 'postal_code')
    ordering = ('user__email', '-is_default')
    
    def user_email(self, obj):
        return obj.user.email
    user_email.admin_order_field = 'user__email'
    user_email.short_description = 'User'

    fieldsets = (
        ('User', {
            'fields': ('user',)
        }),
        ('Contact Information', {
            'fields': ('full_name', 'phone')
        }),
        ('Address Details', {
            'fields': (
                'address_type',
                'street_address1',
                'street_address2',
                ('city', 'state'),
                ('postal_code', 'country'),
                'is_default'
            )
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ('created_at', 'updated_at')

class UserPreferenceAdmin(SecureModelAdmin):
    list_display = ('user_email', 'theme', 'email_notif_status', 'push_notif_status', 'wishlist_count', 'saved_items_count')
    list_filter = ('theme', 'email_notifications', 'push_notifications')
    search_fields = ('user__email',)
    filter_horizontal = ('preferred_categories', 'wishlist_items', 'saved_items')
    readonly_fields = ('created_at', 'updated_at', 'wishlist_count', 'saved_items_count')

    def user_email(self, obj):
        return obj.user.email
    user_email.admin_order_field = 'user__email'
    user_email.short_description = 'User'

    def email_notif_status(self, obj):
        status_colors = {
            'all': 'green',
            'important': 'orange',
            'none': 'red'
        }
        return format_html(
            '<span style="color: {};">{}</span>',
            status_colors.get(obj.email_notifications, 'black'),
            obj.get_email_notifications_display()
        )
    email_notif_status.short_description = 'Email Notifications'

    def push_notif_status(self, obj):
        status_colors = {
            'all': 'green',
            'important': 'orange',
            'none': 'red'
        }
        return format_html(
            '<span style="color: {};">{}</span>',
            status_colors.get(obj.push_notifications, 'black'),
            obj.get_push_notifications_display()
        )
    push_notif_status.short_description = 'Push Notifications'

    def wishlist_count(self, obj):
        count = obj.wishlist_items.count()
        if count > 0:
            url = reverse('admin:products_product_changelist') + f'?id__in={",".join(str(id) for id in obj.wishlist_items.values_list("id", flat=True))}'
            return format_html('<a href="{}">{} items</a>', url, count)
        return '0 items'
    wishlist_count.short_description = 'Wishlist'

    def saved_items_count(self, obj):
        count = obj.saved_items.count()
        if count > 0:
            url = reverse('admin:products_product_changelist') + f'?id__in={",".join(str(id) for id in obj.saved_items.values_list("id", flat=True))}'
            return format_html('<a href="{}">{} items</a>', url, count)
        return '0 items'
    saved_items_count.short_description = 'Saved Items'

    fieldsets = (
        ('User', {
            'fields': ('user',),
            'classes': ('wide',)
        }),
        ('Display & Notifications', {
            'fields': (
                'theme',
                ('email_notifications', 'push_notifications'),
            ),
            'classes': ('wide',)
        }),
        ('Shopping Preferences', {
            'fields': (
                ('default_shipping_address', 'default_billing_address'),
                'preferred_categories',
            ),
            'classes': ('wide',)
        }),
        ('Saved Products', {
            'fields': (
                ('wishlist_count', 'saved_items_count'),
                'wishlist_items',
                'saved_items',
            ),
            'classes': ('wide',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

# Register with both default admin site and secure admin site
admin.site.register(User, SecureUserAdmin)
admin.site.register(Address, AddressAdmin)
admin.site.register(UserPreference, UserPreferenceAdmin)

secure_admin_site.register(User, SecureUserAdmin)
secure_admin_site.register(Address, AddressAdmin)
secure_admin_site.register(UserPreference, UserPreferenceAdmin)
