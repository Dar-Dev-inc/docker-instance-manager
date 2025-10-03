from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator


class Profile(models.Model):
    """Extended user profile with instance limits and roles"""
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('developer', 'Developer'),
        ('viewer', 'Viewer'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    max_instances = models.IntegerField(default=5, validators=[MinValueValidator(1)])
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='developer')

    def __str__(self):
        return f"{self.user.username} - {self.role}"


class Template(models.Model):
    """Docker container templates for launching instances"""
    name = models.CharField(max_length=100, unique=True)
    docker_image = models.CharField(max_length=200)
    default_ports = models.JSONField(
        default=dict,
        help_text='Port mapping dictionary, e.g., {"vscode": 8080, "jupyter": 8888}'
    )
    description = models.TextField(blank=True)
    cpu_limit = models.FloatField(
        default=1.0,
        validators=[MinValueValidator(0.1)],
        help_text='CPU cores limit'
    )
    memory_limit = models.IntegerField(
        default=1024,
        validators=[MinValueValidator(128)],
        help_text='Memory limit in MB'
    )
    environment_vars = models.JSONField(
        default=dict,
        blank=True,
        help_text='Default environment variables'
    )
    volume_mounts = models.JSONField(
        default=dict,
        blank=True,
        help_text='Volume mount paths, e.g., {"/workspace": "/home/coder/project", "/data": "/var/lib/data"}'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class Instance(models.Model):
    """Running or stopped Docker container instances"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('running', 'Running'),
        ('stopped', 'Stopped'),
        ('error', 'Error'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='instances')
    template = models.ForeignKey(Template, on_delete=models.CASCADE, related_name='instances')
    name = models.CharField(max_length=100, blank=True)
    container_id = models.CharField(max_length=64, blank=True, null=True)
    host_ports = models.JSONField(
        default=dict,
        help_text='Assigned host ports mapping, e.g., {"vscode": 49152}'
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    error_message = models.TextField(blank=True)
    environment_vars = models.JSONField(default=dict, blank=True)
    volume_name = models.CharField(max_length=200, blank=True, null=True, help_text='Docker volume name for persistent storage')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.template.name} ({self.status})"

    def get_service_urls(self):
        """Generate URLs for accessing services in the container"""
        urls = {}
        for service_name, port in self.host_ports.items():
            urls[service_name] = f"http://localhost:{port}"
        return urls


class AuditLog(models.Model):
    """Track user actions for security and debugging"""
    ACTION_CHOICES = [
        ('create', 'Create Instance'),
        ('start', 'Start Instance'),
        ('stop', 'Stop Instance'),
        ('delete', 'Delete Instance'),
        ('create_template', 'Create Template'),
        ('update_template', 'Update Template'),
        ('delete_template', 'Delete Template'),
    ]

    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    instance = models.ForeignKey(Instance, on_delete=models.SET_NULL, null=True, blank=True)
    template = models.ForeignKey(Template, on_delete=models.SET_NULL, null=True, blank=True)
    details = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.user} - {self.action} at {self.timestamp}"
