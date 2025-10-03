"""Views for the Docker management application"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.generic import ListView, DetailView, CreateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.http import JsonResponse
from django.contrib.auth.models import User
from django.db.models import Count, Q
from core.models import Instance, Template, AuditLog, Profile
from core.tasks import create_instance_task, stop_instance_task, restart_instance_task, delete_instance_task
from core.services.docker_manager import DockerManager
from core.decorators import admin_required


@login_required
def dashboard(request):
    """Main dashboard showing user's instances"""
    instances = Instance.objects.filter(user=request.user).select_related('template')
    templates = Template.objects.all()

    context = {
        'instances': instances,
        'templates': templates,
    }
    return render(request, 'core/dashboard.html', context)


@login_required
def instance_detail(request, instance_id):
    """Detailed view of a single instance"""
    instance = get_object_or_404(Instance, id=instance_id, user=request.user)

    # Get container logs if container exists
    logs = ""
    if instance.container_id:
        docker_manager = DockerManager()
        logs = docker_manager.get_container_logs(instance.container_id, tail=100)

    context = {
        'instance': instance,
        'logs': logs,
        'service_urls': instance.get_service_urls(),
    }
    return render(request, 'core/instance_detail.html', context)


@login_required
def create_instance(request, template_id):
    """Create a new instance from a template"""
    template = get_object_or_404(Template, id=template_id)

    # Check if user has reached instance limit
    user_profile = getattr(request.user, 'profile', None)
    if user_profile:
        active_instances = Instance.objects.filter(
            user=request.user,
            status__in=['running', 'pending']
        ).count()

        if active_instances >= user_profile.max_instances:
            messages.error(
                request,
                f"You have reached your instance limit ({user_profile.max_instances}). "
                "Please stop or delete an existing instance."
            )
            return redirect('dashboard')

    if request.method == 'POST':
        # Create instance
        instance_name = request.POST.get('name', '')
        instance = Instance.objects.create(
            user=request.user,
            template=template,
            name=instance_name,
            status='pending'
        )

        # Trigger async task to start container
        create_instance_task.delay(instance.id)

        messages.success(
            request,
            f"Instance '{instance_name or template.name}' is being created. "
            "This may take a few moments."
        )
        return redirect('dashboard')

    context = {
        'template': template,
    }
    return render(request, 'core/create_instance.html', context)


@login_required
def stop_instance(request, instance_id):
    """Stop a running instance"""
    instance = get_object_or_404(Instance, id=instance_id, user=request.user)

    if instance.status != 'running':
        messages.warning(request, "Instance is not running.")
        return redirect('dashboard')

    # Trigger async task to stop container
    stop_instance_task.delay(instance.id)
    instance.status = 'pending'
    instance.save()

    messages.success(request, f"Stopping instance '{instance.name or instance.template.name}'...")
    return redirect('dashboard')


@login_required
def restart_instance(request, instance_id):
    """Restart an instance"""
    instance = get_object_or_404(Instance, id=instance_id, user=request.user)

    if instance.status not in ['running', 'stopped']:
        messages.warning(request, "Instance cannot be restarted in current state.")
        return redirect('dashboard')

    # Trigger async task to restart container
    restart_instance_task.delay(instance.id)
    instance.status = 'pending'
    instance.save()

    messages.success(request, f"Restarting instance '{instance.name or instance.template.name}'...")
    return redirect('dashboard')


@login_required
def delete_instance(request, instance_id):
    """Delete an instance"""
    instance = get_object_or_404(Instance, id=instance_id, user=request.user)

    if request.method == 'POST':
        instance_name = instance.name or instance.template.name
        delete_volume = request.POST.get('delete_volume') == 'on'

        # Trigger async task to delete container and instance
        delete_instance_task.delay(instance.id, request.user.id, delete_volume)

        if delete_volume:
            messages.success(request, f"Deleting instance '{instance_name}' and its data volume...")
        else:
            messages.success(request, f"Deleting instance '{instance_name}' (data volume will be preserved)...")
        return redirect('dashboard')

    context = {
        'instance': instance,
    }
    return render(request, 'core/confirm_delete.html', context)


@login_required
def instance_status_api(request, instance_id):
    """API endpoint to get current instance status"""
    instance = get_object_or_404(Instance, id=instance_id, user=request.user)

    # Sync status with Docker if container exists
    if instance.container_id and instance.status != 'error':
        docker_manager = DockerManager()
        docker_status = docker_manager.get_container_status(instance.container_id)

        # Map Docker status to our status
        status_map = {
            'running': 'running',
            'exited': 'stopped',
            'created': 'pending',
            'restarting': 'pending',
            'paused': 'stopped',
            'dead': 'error',
            'not_found': 'error',
        }

        mapped_status = status_map.get(docker_status, 'error')
        if instance.status != mapped_status:
            instance.status = mapped_status
            instance.save()

    return JsonResponse({
        'status': instance.status,
        'error_message': instance.error_message,
        'service_urls': instance.get_service_urls(),
    })


class TemplateListView(LoginRequiredMixin, ListView):
    """List all available templates"""
    model = Template
    template_name = 'core/template_list.html'
    context_object_name = 'templates'


class AuditLogListView(LoginRequiredMixin, ListView):
    """View audit logs for the current user"""
    model = AuditLog
    template_name = 'core/audit_log.html'
    context_object_name = 'logs'
    paginate_by = 50

    def get_queryset(self):
        return AuditLog.objects.filter(user=self.request.user)


# ============================================================================
# ADMIN VIEWS - For platform administrators to manage all users and instances
# ============================================================================

@admin_required
def admin_overview(request):
    """Admin dashboard showing platform-wide statistics"""
    # User statistics
    total_users = User.objects.count()
    active_users = User.objects.filter(instances__status='running').distinct().count()

    # Instance statistics
    total_instances = Instance.objects.count()
    running_instances = Instance.objects.filter(status='running').count()
    stopped_instances = Instance.objects.filter(status='stopped').count()
    error_instances = Instance.objects.filter(status='error').count()

    # Template statistics
    total_templates = Template.objects.count()
    templates_with_volumes = Template.objects.exclude(volume_mounts={}).count()

    # Recent activity
    recent_instances = Instance.objects.select_related('user', 'template').order_by('-created_at')[:10]
    recent_logs = AuditLog.objects.select_related('user').order_by('-timestamp')[:15]

    # User instance counts
    user_stats = User.objects.annotate(
        total_instances=Count('instances'),
        running=Count('instances', filter=Q(instances__status='running')),
        stopped=Count('instances', filter=Q(instances__status='stopped'))
    ).order_by('-total_instances')[:10]

    context = {
        'total_users': total_users,
        'active_users': active_users,
        'total_instances': total_instances,
        'running_instances': running_instances,
        'stopped_instances': stopped_instances,
        'error_instances': error_instances,
        'total_templates': total_templates,
        'templates_with_volumes': templates_with_volumes,
        'recent_instances': recent_instances,
        'recent_logs': recent_logs,
        'user_stats': user_stats,
    }

    return render(request, 'core/admin_overview.html', context)


@admin_required
def admin_users(request):
    """Admin view to manage all users"""
    users = User.objects.select_related('profile').annotate(
        instance_count=Count('instances'),
        running_count=Count('instances', filter=Q(instances__status='running'))
    ).order_by('-date_joined')

    context = {
        'users': users,
    }
    return render(request, 'core/admin_users.html', context)


@admin_required
def admin_user_detail(request, user_id):
    """Admin view to see specific user details"""
    user = get_object_or_404(User, id=user_id)
    instances = Instance.objects.filter(user=user).select_related('template').order_by('-created_at')
    logs = AuditLog.objects.filter(user=user).order_by('-timestamp')[:20]

    context = {
        'viewed_user': user,
        'instances': instances,
        'logs': logs,
    }
    return render(request, 'core/admin_user_detail.html', context)


@admin_required
def admin_all_instances(request):
    """Admin view to see all instances across all users"""
    status_filter = request.GET.get('status', 'all')
    user_filter = request.GET.get('user', None)

    instances = Instance.objects.select_related('user', 'template').order_by('-created_at')

    if status_filter != 'all':
        instances = instances.filter(status=status_filter)

    if user_filter:
        instances = instances.filter(user_id=user_filter)

    # Get all users for filter dropdown
    users = User.objects.order_by('username')

    context = {
        'instances': instances,
        'users': users,
        'current_status': status_filter,
        'current_user': user_filter,
    }
    return render(request, 'core/admin_all_instances.html', context)


@admin_required
def admin_update_user_quota(request, user_id):
    """Admin endpoint to update user quotas"""
    user = get_object_or_404(User, id=user_id)

    if request.method == 'POST':
        max_instances = request.POST.get('max_instances')
        role = request.POST.get('role')

        if max_instances:
            user.profile.max_instances = int(max_instances)
        if role:
            user.profile.role = role

        user.profile.save()
        messages.success(request, f"Updated quotas for {user.username}")
        return redirect('admin_user_detail', user_id=user.id)

    return redirect('admin_users')
