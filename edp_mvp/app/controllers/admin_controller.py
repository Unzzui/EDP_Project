from flask import Blueprint, render_template, redirect, url_for, request, flash, session
from flask_login import login_required, current_user
from functools import wraps
from ..models.user import User
from ..extensions import db

# Create admin blueprint
admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

def role_required(required_role):
    """Decorator to require specific role."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Get user role from session
            user_role = session.get('user_role', 'guest')
            if user_role != required_role:
                flash('No tienes permisos para acceder a esta página.', 'error')
                return redirect(url_for('auth.login'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

@admin_bp.route('/usuarios')
@login_required
@role_required('admin')
def usuarios():
    """List all users."""
    users = User.get_all_active()
    stats = User.get_stats()
    return render_template('admin/usuarios/index.html', users=users, stats=stats)

@admin_bp.route('/usuarios/nuevo', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def nuevo_usuario():
    """Create new user."""
    if request.method == 'POST':
        # Get form data
        nombre_completo = request.form.get('nombre_completo', '').strip()
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        rol = request.form.get('rol', '').strip()
        
        # Validate required fields
        if not all([nombre_completo, username, password, rol]):
            flash('Todos los campos son requeridos.', 'error')
            return render_template('admin/usuarios/nuevo.html')
        
        # Validate role
        valid_roles = ['admin', 'controller', 'manager', 'jefe_proyecto']
        if rol not in valid_roles:
            flash('Rol inválido seleccionado.', 'error')
            return render_template('admin/usuarios/nuevo.html')
        
        # Create user
        user, message = User.create_user(nombre_completo, username, password, rol)
        
        if user:
            flash(message, 'success')
            return redirect(url_for('admin.usuarios'))
        else:
            flash(message, 'error')
            return render_template('admin/usuarios/nuevo.html')
    
    return render_template('admin/usuarios/nuevo.html') 