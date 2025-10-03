"""Custom decorators for access control"""
from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages


def admin_required(view_func):
    """Decorator to require admin role"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')

        # Check if user has admin role in their profile
        if hasattr(request.user, 'profile') and request.user.profile.role == 'admin':
            return view_func(request, *args, **kwargs)

        # Also allow Django superusers
        if request.user.is_superuser:
            return view_func(request, *args, **kwargs)

        messages.error(request, "You don't have permission to access this page. Admin access required.")
        return redirect('dashboard')

    return wrapper
