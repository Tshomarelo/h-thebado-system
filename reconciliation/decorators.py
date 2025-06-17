from functools import wraps
from django.core.exceptions import PermissionDenied
from django.contrib.auth.decorators import user_passes_test

def role_required(allowed_roles=[]):
    """
    Decorator for views that checks that the user has one of the allowed roles.
    Assumes user model has a 'role' attribute.
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                raise PermissionDenied # Or redirect to login
            if request.user.role in allowed_roles or request.user.is_superuser:
                return view_func(request, *args, **kwargs)
            else:
                raise PermissionDenied
        return _wrapped_view
    return decorator

def manager_or_higher_required(view_func):
    """
    Decorator for views that requires the user to be a Manager, Senior Manager, or CEO.
    """
    allowed_roles = ['MANAGER', 'SENIOR_MANAGER', 'CEO']
    actual_decorator = user_passes_test(
        lambda u: u.is_authenticated and (u.role in allowed_roles or u.is_superuser),
        login_url='users:login', # Redirect to login if test fails
        redirect_field_name=None
    )
    return actual_decorator(view_func)