from flask import Blueprint, render_template, redirect, url_for, request, flash, session, jsonify
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
    show_all = request.args.get('show_all', 'false').lower() == 'true'
    
    if show_all:
        users = User.get_all()
    else:
        users = User.get_all_active()
    
    stats = User.get_stats()
    return render_template('admin/usuarios/index.html', users=users, stats=stats, show_all=show_all)

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
        jefe_asignado = request.form.get('jefe_asignado', '').strip()
        
        # Validate required fields
        if not all([nombre_completo, username, password, rol]):
            flash('Todos los campos son requeridos.', 'error')
            jefes_proyecto = User.get_jefes_proyecto()
            return render_template('admin/usuarios/nuevo.html', jefes_proyecto=jefes_proyecto)
        
        # Validate role
        valid_roles = ['admin', 'controller', 'manager', 'jefe_proyecto', 'miembro_equipo_proyecto']
        if rol not in valid_roles:
            flash('Rol inválido seleccionado.', 'error')
            jefes_proyecto = User.get_jefes_proyecto()
            return render_template('admin/usuarios/nuevo.html', jefes_proyecto=jefes_proyecto)
        
        # If role requires a jefe_asignado, validate it's provided
        if rol in ['jefe_proyecto', 'miembro_equipo_proyecto'] and not jefe_asignado:
            flash('Debe seleccionar un jefe de proyecto para este rol.', 'error')
            jefes_proyecto = User.get_jefes_proyecto()
            return render_template('admin/usuarios/nuevo.html', jefes_proyecto=jefes_proyecto)
        
        # Create user
        user, message = User.create_user(nombre_completo, username, password, rol, jefe_asignado if jefe_asignado else None)
        
        if user:
            flash(message, 'success')
            return redirect(url_for('admin.usuarios'))
        else:
            flash(message, 'error')
            jefes_proyecto = User.get_jefes_proyecto()
            return render_template('admin/usuarios/nuevo.html', jefes_proyecto=jefes_proyecto)
    
    # GET request - show form
    jefes_proyecto = User.get_jefes_proyecto()
    return render_template('admin/usuarios/nuevo.html', jefes_proyecto=jefes_proyecto)

@admin_bp.route('/usuarios/<int:user_id>/editar', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def editar_usuario(user_id):
    """Edit existing user."""
    user = User.get_by_id(user_id)
    if not user:
        flash('Usuario no encontrado.', 'error')
        return redirect(url_for('admin.usuarios'))
    
    # Prevent admin from editing themselves (could lock themselves out)
    if user.id == current_user.id:
        flash('No puedes editar tu propio usuario.', 'warning')
        return redirect(url_for('admin.usuarios'))
    
    if request.method == 'POST':
        # Get form data
        nombre_completo = request.form.get('nombre_completo', '').strip()
        username = request.form.get('username', '').strip()
        rol = request.form.get('rol', '').strip()
        jefe_asignado = request.form.get('jefe_asignado', '').strip()
        new_password = request.form.get('new_password', '').strip()
        
        # Validate required fields
        if not all([nombre_completo, username, rol]):
            flash('Nombre completo, usuario y rol son requeridos.', 'error')
            jefes_proyecto = User.get_jefes_proyecto()
            return render_template('admin/usuarios/editar.html', user=user, jefes_proyecto=jefes_proyecto)
        
        # Validate role
        valid_roles = ['admin', 'controller', 'manager', 'jefe_proyecto', 'miembro_equipo_proyecto']
        if rol not in valid_roles:
            flash('Rol inválido seleccionado.', 'error')
            jefes_proyecto = User.get_jefes_proyecto()
            return render_template('admin/usuarios/editar.html', user=user, jefes_proyecto=jefes_proyecto)
        
        # If role requires a jefe_asignado, validate it's provided
        if rol in ['jefe_proyecto', 'miembro_equipo_proyecto'] and not jefe_asignado:
            flash('Debe seleccionar un jefe de proyecto para este rol.', 'error')
            jefes_proyecto = User.get_jefes_proyecto()
            return render_template('admin/usuarios/editar.html', user=user, jefes_proyecto=jefes_proyecto)
        
        # Update user information
        success, message = user.update_user_info(nombre_completo, username, rol, jefe_asignado if jefe_asignado else None)
        
        if not success:
            flash(message, 'error')
            jefes_proyecto = User.get_jefes_proyecto()
            return render_template('admin/usuarios/editar.html', user=user, jefes_proyecto=jefes_proyecto)
        
        # Update password if provided
        if new_password:
            user.set_password(new_password)
            try:
                db.session.commit()
            except Exception as e:
                db.session.rollback()
                flash(f'Error al actualizar la contraseña: {str(e)}', 'error')
                jefes_proyecto = User.get_jefes_proyecto()
                return render_template('admin/usuarios/editar.html', user=user, jefes_proyecto=jefes_proyecto)
        
        flash(message, 'success')
        return redirect(url_for('admin.usuarios'))
    
    # GET request - show form
    jefes_proyecto = User.get_jefes_proyecto()
    return render_template('admin/usuarios/editar.html', user=user, jefes_proyecto=jefes_proyecto)

@admin_bp.route('/usuarios/<int:user_id>/desactivar', methods=['POST'])
@login_required
@role_required('admin')
def desactivar_usuario(user_id):
    """Deactivate user account."""
    if request.is_json:
        # Handle AJAX request
        user = User.get_by_id(user_id)
        if not user:
            return jsonify({'success': False, 'message': 'Usuario no encontrado'}), 404
        
        # Prevent admin from deactivating themselves
        if user.id == current_user.id:
            return jsonify({'success': False, 'message': 'No puedes desactivar tu propio usuario'}), 400
        
        if not user.activo:
            return jsonify({'success': False, 'message': 'El usuario ya está desactivado'}), 400
        
        success, message = user.deactivate()
        
        if success:
            return jsonify({'success': True, 'message': message}), 200
        else:
            return jsonify({'success': False, 'message': message}), 500
    else:
        # Handle regular form submission
        user = User.get_by_id(user_id)
        if not user:
            flash('Usuario no encontrado.', 'error')
            return redirect(url_for('admin.usuarios'))
        
        # Prevent admin from deactivating themselves
        if user.id == current_user.id:
            flash('No puedes desactivar tu propio usuario.', 'warning')
            return redirect(url_for('admin.usuarios'))
        
        if not user.activo:
            flash('El usuario ya está desactivado.', 'warning')
            return redirect(url_for('admin.usuarios'))
        
        success, message = user.deactivate()
        flash(message, 'success' if success else 'error')
        
        return redirect(url_for('admin.usuarios'))

@admin_bp.route('/usuarios/<int:user_id>/activar', methods=['POST'])
@login_required
@role_required('admin')
def activar_usuario(user_id):
    """Activate user account."""
    if request.is_json:
        # Handle AJAX request
        user = User.get_by_id(user_id)
        if not user:
            return jsonify({'success': False, 'message': 'Usuario no encontrado'}), 404
        
        if user.activo:
            return jsonify({'success': False, 'message': 'El usuario ya está activo'}), 400
        
        success, message = user.activate()
        
        if success:
            return jsonify({'success': True, 'message': message}), 200
        else:
            return jsonify({'success': False, 'message': message}), 500
    else:
        # Handle regular form submission
        user = User.get_by_id(user_id)
        if not user:
            flash('Usuario no encontrado.', 'error')
            return redirect(url_for('admin.usuarios'))
        
        if user.activo:
            flash('El usuario ya está activo.', 'warning')
            return redirect(url_for('admin.usuarios'))
        
        success, message = user.activate()
        flash(message, 'success' if success else 'error')
        
        return redirect(url_for('admin.usuarios'))

@admin_bp.route('/usuarios/<int:user_id>/eliminar', methods=['POST'])
@login_required
@role_required('admin')
def eliminar_usuario(user_id):
    """Delete user account (actually just deactivate)."""
    # For security, we just deactivate instead of actually deleting
    return desactivar_usuario(user_id)