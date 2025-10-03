"""Admin interface configuration for Docker Manager"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from core.models import Profile, Template, Instance, AuditLog


class ProfileInline(admin.StackedInline):
    """Inline admin for Profile"""
    model = Profile
    can_delete = False
    verbose_name_plural = 'Profile'
    fields = ('max_instances', 'role')


class UserAdmin(BaseUserAdmin):
    """Extended User admin with Profile inline"""
    inlines = (ProfileInline,)


# Re-register UserAdmin
admin.site.unregister(User)
admin.site.register(User, UserAdmin)


@admin.register(Template)
class TemplateAdmin(admin.ModelAdmin):
    """Admin interface for Template model"""
    list_display = ('name', 'docker_image', 'cpu_limit', 'memory_limit', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('name', 'docker_image', 'description')
    readonly_fields = ('created_at', 'updated_at')

    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'docker_image', 'description')
        }),
        ('Resource Limits', {
            'fields': ('cpu_limit', 'memory_limit')
        }),
        ('Configuration', {
            'fields': ('default_ports', 'environment_vars', 'volume_mounts'),
            'description': 'volume_mounts example: {"workspace": "/home/coder/project", "data": "/var/lib/data"}'
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Instance)
class InstanceAdmin(admin.ModelAdmin):
    """Admin interface for Instance model"""
    list_display = ('get_instance_name', 'user', 'template', 'status', 'get_volume_display', 'created_at')
    list_filter = ('status', 'created_at', 'template', 'user')
    search_fields = ('name', 'user__username', 'template__name', 'container_id', 'volume_name')
    readonly_fields = ('container_id', 'volume_name', 'created_at', 'updated_at')

    fieldsets = (
        ('Basic Information', {
            'fields': ('user', 'template', 'name', 'status')
        }),
        ('Container Details', {
            'fields': ('container_id', 'host_ports', 'environment_vars')
        }),
        ('Persistent Storage', {
            'fields': ('volume_name',),
            'description': 'Docker volume for persistent data storage'
        }),
        ('Error Information', {
            'fields': ('error_message',),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def get_instance_name(self, obj):
        """Display instance name or template name"""
        return obj.name or f"{obj.template.name} (#{obj.id})"
    get_instance_name.short_description = 'Instance'

    def get_volume_display(self, obj):
        """Display volume name with icon"""
        if obj.volume_name:
            return f"✓ {obj.volume_name}"
        return "—"
    get_volume_display.short_description = 'Volume'

    actions = ['mark_as_stopped', 'mark_as_error']

    def mark_as_stopped(self, request, queryset):
        """Bulk action to mark instances as stopped"""
        updated = queryset.update(status='stopped')
        self.message_user(request, f"{updated} instances marked as stopped.")
    mark_as_stopped.short_description = "Mark selected as stopped"

    def mark_as_error(self, request, queryset):
        """Bulk action to mark instances as error"""
        updated = queryset.update(status='error')
        self.message_user(request, f"{updated} instances marked as error.")
    mark_as_error.short_description = "Mark selected as error"


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    """Admin interface for AuditLog model"""
    list_display = ('user', 'action', 'timestamp', 'get_target')
    list_filter = ('action', 'timestamp')
    search_fields = ('user__username', 'details')
    readonly_fields = ('user', 'action', 'instance', 'template', 'details', 'timestamp')

    def get_target(self, obj):
        """Display the target of the action"""
        if obj.instance:
            return f"Instance: {obj.instance}"
        elif obj.template:
            return f"Template: {obj.template}"
        return "—"
    get_target.short_description = 'Target'

    def has_add_permission(self, request):
        """Disable manual creation of audit logs"""
        return False

    def has_change_permission(self, request, obj=None):
        """Make audit logs read-only"""
        return False


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    """Admin interface for Profile model"""
    list_display = ('user', 'role', 'max_instances')
    list_filter = ('role',)
    search_fields = ('user__username',)
