# Generated migration file

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.core.validators


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Profile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('max_instances', models.IntegerField(default=5, validators=[django.core.validators.MinValueValidator(1)])),
                ('role', models.CharField(choices=[('admin', 'Admin'), ('developer', 'Developer'), ('viewer', 'Viewer')], default='developer', max_length=20)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='profile', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Template',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, unique=True)),
                ('docker_image', models.CharField(max_length=200)),
                ('default_ports', models.JSONField(default=dict, help_text='Port mapping dictionary, e.g., {"vscode": 8080, "jupyter": 8888}')),
                ('description', models.TextField(blank=True)),
                ('cpu_limit', models.FloatField(default=1.0, help_text='CPU cores limit', validators=[django.core.validators.MinValueValidator(0.1)])),
                ('memory_limit', models.IntegerField(default=1024, help_text='Memory limit in MB', validators=[django.core.validators.MinValueValidator(128)])),
                ('environment_vars', models.JSONField(blank=True, default=dict, help_text='Default environment variables')),
                ('volume_mounts', models.JSONField(blank=True, default=dict, help_text='Volume mount paths, e.g., {"/workspace": "/home/coder/project", "/data": "/var/lib/data"}')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='Instance',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(blank=True, max_length=100)),
                ('container_id', models.CharField(blank=True, max_length=64, null=True)),
                ('host_ports', models.JSONField(default=dict, help_text='Assigned host ports mapping, e.g., {"vscode": 49152}')),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('running', 'Running'), ('stopped', 'Stopped'), ('error', 'Error')], default='pending', max_length=20)),
                ('error_message', models.TextField(blank=True)),
                ('environment_vars', models.JSONField(blank=True, default=dict)),
                ('volume_name', models.CharField(blank=True, help_text='Docker volume name for persistent storage', max_length=200, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('template', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='instances', to='core.template')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='instances', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='Volume',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('host_path', models.CharField(max_length=500)),
                ('container_path', models.CharField(max_length=500)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('instance', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='volumes', to='core.instance')),
            ],
        ),
        migrations.CreateModel(
            name='AuditLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('action', models.CharField(choices=[('create', 'Create Instance'), ('start', 'Start Instance'), ('stop', 'Stop Instance'), ('delete', 'Delete Instance'), ('create_template', 'Create Template'), ('update_template', 'Update Template'), ('delete_template', 'Delete Template')], max_length=20)),
                ('details', models.TextField(blank=True)),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('instance', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='core.instance')),
                ('template', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='core.template')),
                ('user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-timestamp'],
            },
        ),
    ]
