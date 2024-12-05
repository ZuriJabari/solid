from django.contrib import admin
from django.contrib.admin.models import LogEntry
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.mixins import UserPassesTestMixin
from django.core.exceptions import PermissionDenied
from config.audit import log_action

class LogEntryAdmin(admin.ModelAdmin):
    list_display = [
        'action_time',
        'user',
        'content_type',
        'object_repr',
        'action_flag',
        'change_message'
    ]
    list_filter = [
        'action_time',
        'user',
        'content_type',
        'action_flag'
    ]
    search_fields = [
        'object_repr',
        'change_message'
    ]
    date_hierarchy = 'action_time'
    readonly_fields = [
        'action_time',
        'user',
        'content_type',
        'object_id',
        'object_repr',
        'action_flag',
        'change_message'
    ]

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

# Register the LogEntry model
admin.site.register(LogEntry, LogEntryAdmin)

# Configure the default admin site
admin.site.site_header = _('Urban Herb Administration')
admin.site.site_title = _('Urban Herb Admin')
admin.site.index_title = _('Administration')

class SecureModelAdmin(admin.ModelAdmin):
    """
    Base admin class with enhanced security features
    """
    def save_model(self, request, obj, form, change):
        """Log all save operations"""
        super().save_model(request, obj, form, change)
        action_flag = 1 if not change else 2  # 1=Addition, 2=Change
        log_action(request.user, obj, action_flag, str(form.changed_data))

    def delete_model(self, request, obj):
        """Log all delete operations"""
        log_action(request.user, obj, 3, "Deleted object")  # 3=Deletion
        super().delete_model(request, obj)

    def has_module_permission(self, request):
        """Check if user has required permissions"""
        if not super().has_module_permission(request):
            return False
        return True

# Custom admin site with security enhancements
class SecureAdminSite(admin.AdminSite):
    site_header = _('Urban Herb Administration')
    site_title = _('Urban Herb Admin')
    index_title = _('Administration')
    
    def has_permission(self, request):
        """
        Enhanced permission check for admin site access
        """
        # Check if user is authenticated and is staff
        if not request.user.is_authenticated or not request.user.is_staff:
            return False
        return True

# Create a custom admin site instance
secure_admin_site = SecureAdminSite(name='secure_admin') 