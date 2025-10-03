"""URL configuration for core app"""
from django.urls import path
from core import views

urlpatterns = [
    # User dashboard and instance management
    path('', views.dashboard, name='dashboard'),
    path('templates/', views.TemplateListView.as_view(), name='template_list'),
    path('instance/<int:instance_id>/', views.instance_detail, name='instance_detail'),
    path('instance/create/<int:template_id>/', views.create_instance, name='create_instance'),
    path('instance/<int:instance_id>/stop/', views.stop_instance, name='stop_instance'),
    path('instance/<int:instance_id>/restart/', views.restart_instance, name='restart_instance'),
    path('instance/<int:instance_id>/delete/', views.delete_instance, name='delete_instance'),
    path('api/instance/<int:instance_id>/status/', views.instance_status_api, name='instance_status_api'),
    path('audit-logs/', views.AuditLogListView.as_view(), name='audit_logs'),

    # Admin-only URLs
    path('admin-dashboard/', views.admin_overview, name='admin_overview'),
    path('admin-dashboard/users/', views.admin_users, name='admin_users'),
    path('admin-dashboard/users/<int:user_id>/', views.admin_user_detail, name='admin_user_detail'),
    path('admin-dashboard/instances/', views.admin_all_instances, name='admin_all_instances'),
    path('admin-dashboard/users/<int:user_id>/update-quota/', views.admin_update_user_quota, name='admin_update_user_quota'),
]
