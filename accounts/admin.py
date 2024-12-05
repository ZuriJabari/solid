from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Address, UserPreference
from config.admin import SecureModelAdmin, secure_admin_site

class AddressInline(admin.StackedInline):
    model = Address
    extra = 0

class UserPreferenceInline(admin.StackedInline):
    model = UserPreference
    can_delete = False

class SecureUserAdmin(UserAdmin, SecureModelAdmin):
    list_display = ('email', 'first_name', 'last_name', 'is_staff', 'is_active', 'date_joined')
    list_filter = ('is_staff', 'is_active', 'groups')
    search_fields = ('email', 'first_name', 'last_name')
    ordering = ('email',)
    inlines = [AddressInline, UserPreferenceInline]
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'phone', 'date_of_birth')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
        ('Email settings', {'fields': ('email_verified', 'newsletter_subscribed', 'marketing_preferences')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'first_name', 'last_name', 'password1', 'password2'),
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
    list_display = ('user', 'address_type', 'city', 'state', 'is_default')
    list_filter = ('address_type', 'is_default', 'state')
    search_fields = ('user__email', 'full_name', 'city', 'state')

class UserPreferenceAdmin(SecureModelAdmin):
    list_display = ('user', 'theme')
    list_filter = ('theme',)
    search_fields = ('user__email',)

# Register with both default admin site and secure admin site
admin.site.register(User, SecureUserAdmin)
admin.site.register(Address, AddressAdmin)
admin.site.register(UserPreference, UserPreferenceAdmin)

secure_admin_site.register(User, SecureUserAdmin)
secure_admin_site.register(Address, AddressAdmin)
secure_admin_site.register(UserPreference, UserPreferenceAdmin)
