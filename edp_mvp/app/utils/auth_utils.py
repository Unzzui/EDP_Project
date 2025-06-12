"""
Authentication utilities for the EDP Management System.
Provides decorators and utilities for login and role-based access control.
"""

from functools import wraps
from flask import session, flash, redirect, url_for, request
from flask_login import current_user


# Definir jerarquía de roles
ROLE_HIERARCHY = {
    'admin': 4,      # Máximo nivel - acceso a todo
    'manager': 3,    # Puede acceder a controller y manager
    'controller': 2, # Solo acceso básico
    'jefe_proyecto': 1,  # Puede acceder a sus proyectos y tareas
    'miembro_equipo_proyecto': 1,  # Mismo nivel que jefe_proyecto
    'guest': 0       # Sin acceso
}


def get_user_role_level(user_role):
    """Get the numeric level for a user role."""
    return ROLE_HIERARCHY.get(user_role, 0)


def check_role_hierarchy(user_role, required_level):
    """Check if user role meets the required level."""
    user_level = get_user_role_level(user_role)
    return user_level >= required_level


def role_required(*allowed_roles):
    """
    Decorator to require specific roles for accessing a route.
    Now supports role hierarchy - higher roles can access lower role functions.
    
    Usage:
        @role_required('admin')  # Solo admin
        @role_required('manager')  # Manager y admin
        @role_required('controller')  # Controller, jefe_proyecto, manager y admin
    
    Args:
        allowed_roles: One or more role names that are allowed to access the route
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Check if user is authenticated (should be handled by @login_required first)
            if not current_user.is_authenticated:
                flash('Debes iniciar sesión para acceder a esta página.', 'error')
                return redirect(url_for('auth.login', next=request.url))
            
            # Get user role from session or user object
            user_role = None
            if hasattr(current_user, 'rol'):
                user_role = current_user.rol
            else:
                user_role = session.get('user_role', 'guest')
            
            # Get minimum required level from allowed roles
            required_level = min(get_user_role_level(role) for role in allowed_roles)
            
            # Check if user has required level (hierarchy-based)
            if not check_role_hierarchy(user_role, required_level):
                flash(f'No tienes permisos para acceder a esta página. Rol requerido: {", ".join(allowed_roles)} o superior', 'error')
                # Redirect to appropriate dashboard based on user role
                return redirect(get_redirect_for_role(user_role))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def role_required_exact(*allowed_roles):
    """
    Decorator to require EXACT roles (no hierarchy).
    Use this when you need to restrict to specific roles only.
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash('Debes iniciar sesión para acceder a esta página.', 'error')
                return redirect(url_for('auth.login', next=request.url))
            
            # Get user role
            user_role = None
            if hasattr(current_user, 'rol'):
                user_role = current_user.rol
            else:
                user_role = session.get('user_role', 'guest')
            
            # Check exact role match
            if user_role not in allowed_roles:
                flash(f'No tienes permisos para acceder a esta página. Rol requerido: {", ".join(allowed_roles)}', 'error')
                return redirect(get_redirect_for_role(user_role))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def get_redirect_for_role(user_role):
    """
    Get the appropriate redirect URL based on user role.
    
    Args:
        user_role: The user's role
    
    Returns:
        URL to redirect to based on role
    """
    role_redirects = {
        'admin': 'admin.usuarios',
        'manager': 'manager.dashboard',
        'controller': 'controller.dashboard_controller',
        'jefe_proyecto': 'project_manager.dashboard',
        'miembro_equipo_proyecto': 'project_manager.dashboard',
        'guest': 'auth.login'
    }
    
    try:
        return url_for(role_redirects.get(user_role, 'auth.login'))
    except Exception as e:
        # Fallback if route doesn't exist
        print(f"Error redirecting for role {user_role}: {e}")
        return url_for('auth.login')


def check_user_permission(required_roles, user_role=None):
    """
    Check if current user has permission based on roles (with hierarchy).
    
    Args:
        required_roles: List of required roles
        user_role: Optional user role (will get from current user if not provided)
    
    Returns:
        bool: True if user has permission, False otherwise
    """
    if not current_user.is_authenticated:
        return False
    
    if user_role is None:
        if hasattr(current_user, 'rol'):
            user_role = current_user.rol
        else:
            user_role = session.get('user_role', 'guest')
    
    # Check hierarchy - minimum required level
    required_level = min(get_user_role_level(role) for role in required_roles)
    return check_role_hierarchy(user_role, required_level)


def require_admin(f):
    """Decorator that requires admin role ONLY."""
    return role_required_exact('admin')(f)


def require_manager_or_above(f):
    """Decorator that requires manager or admin role."""
    return role_required('manager')(f)


def require_controller_or_above(f):
    """Decorator that requires controller, jefe_proyecto, manager, or admin role."""
    return role_required('controller')(f)


def require_project_manager_or_above(f):
    """Decorator that requires jefe_proyecto, manager, or admin role."""
    return role_required('jefe_proyecto')(f)


def get_user_context():
    """
    Get current user context for templates.
    
    Returns:
        dict: User context information
    """
    if not current_user.is_authenticated:
        return {
            'is_authenticated': False,
            'role': 'guest',
            'name': 'Invitado',
            'permissions': {},
            'role_level': 0
        }
    
    user_role = getattr(current_user, 'rol', session.get('user_role', 'guest'))
    user_name = getattr(current_user, 'nombre_completo', session.get('user_name', 'Usuario'))
    role_level = get_user_role_level(user_role)
    
    # Define permissions based on role hierarchy
    permissions = {
        'can_view_admin': role_level >= ROLE_HIERARCHY['admin'],
        'can_view_manager': role_level >= ROLE_HIERARCHY['manager'],
        'can_view_controller': role_level >= ROLE_HIERARCHY['controller'],
        'can_edit_users': role_level >= ROLE_HIERARCHY['admin'],
        'can_view_analytics': role_level >= ROLE_HIERARCHY['manager'],
        'can_edit_edps': role_level >= ROLE_HIERARCHY['controller'],
        'can_delete_edps': role_level >= ROLE_HIERARCHY['manager'],
        'can_export_data': role_level >= ROLE_HIERARCHY['controller'],
        'can_manage_system': role_level >= ROLE_HIERARCHY['admin'],
        'can_view_reports': role_level >= ROLE_HIERARCHY['controller'],
        'can_approve_edps': role_level >= ROLE_HIERARCHY['manager'],
    }
    
    return {
        'is_authenticated': True,
        'role': user_role,
        'name': user_name,
        'permissions': permissions,
        'role_level': role_level,
        'user': current_user
    }


def can_access_role_level(required_role):
    """Check if current user can access a specific role level."""
    if not current_user.is_authenticated:
        return False
    
    user_role = getattr(current_user, 'rol', session.get('user_role', 'guest'))
    required_level = get_user_role_level(required_role)
    return check_role_hierarchy(user_role, required_level)


# Template context processor to make user context available in all templates
def inject_user_context():
    """Inject user context into all templates."""
    return {'user_context': get_user_context()} 