from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from .models import User, Address, UserPreference

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('email', 'first_name', 'last_name', 'is_staff', 'is_active', 'email_verified')
    list_filter = ('is_staff', 'is_active', 'email_verified', 'newsletter_subscribed')
    search_fields = ('email', 'first_name', 'last_name')
    ordering = ('email',)
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (_('Personal info'), {
            'fields': (
                'first_name', 'last_name', 'phone',
                'date_of_birth'
            )
        }),
        (_('Email verification'), {
            'fields': (
                'email_verified',
                'email_verification_token'
            )
        }),
        (_('Preferences'), {
            'fields': (
                'newsletter_subscribed',
                'marketing_preferences'
            )
        }),
        (_('Permissions'), {
            'fields': (
                'is_active',
                'is_staff',
                'is_superuser',
                'groups',
                'user_permissions'
            )
        }),
        (_('Important dates'), {
            'fields': ('last_login', 'created_at', 'updated_at')
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at')
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'email', 'password1', 'password2',
                'first_name', 'last_name'
            ),
        }),
    )

@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ('user', 'full_name', 'address_type', 'city', 'state', 'is_default')
    list_filter = ('address_type', 'is_default', 'country', 'state')
    search_fields = ('full_name', 'street_address1', 'city', 'state', 'postal_code')
    raw_id_fields = ('user',)
    
    fieldsets = (
        (_('User'), {
            'fields': ('user',)
        }),
        (_('Address Type'), {
            'fields': ('address_type', 'is_default')
        }),
        (_('Contact Information'), {
            'fields': ('full_name', 'phone')
        }),
        (_('Address Details'), {
            'fields': (
                'street_address1',
                'street_address2',
                'city',
                'state',
                'postal_code',
                'country'
            )
        }),
        (_('Metadata'), {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at')

@admin.register(UserPreference)
class UserPreferenceAdmin(admin.ModelAdmin):
    list_display = ('user', 'theme', 'created_at')
    list_filter = ('theme',)
    search_fields = ('user__email', 'user__first_name', 'user__last_name')
    raw_id_fields = ('user', 'default_shipping_address', 'default_billing_address')
    
    fieldsets = (
        (_('User'), {
            'fields': ('user',)
        }),
        (_('UI Preferences'), {
            'fields': ('theme',)
        }),
        (_('Notification Settings'), {
            'fields': (
                'email_notifications',
                'push_notifications'
            )
        }),
        (_('Default Addresses'), {
            'fields': (
                'default_shipping_address',
                'default_billing_address'
            )
        }),
        (_('Metadata'), {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at')
