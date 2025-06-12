from flask import Blueprint, render_template, redirect, url_for, request, flash, session
from flask_login import login_user, logout_user, login_required, current_user
from ..extensions import login_manager
from .forms import LoginForm
from ..models.user import User
from ..utils.auth_utils import get_redirect_for_role

auth_bp = Blueprint("auth", __name__)


# Esta función es requerida por Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    # Si el usuario ya está autenticado, redirigir al dashboard
    if current_user.is_authenticated:
        # Redirect based on user role using our centralized function
        user_role = session.get('user_role', 'controller')
        return redirect(get_redirect_for_role(user_role))

    # Crear el formulario
    form = LoginForm()
    
    # Si el formulario se envía y valida
    if form.validate_on_submit():
        # Get user from database
        username = form.email.data  # El form usa email pero nosotros lo tratamos como username
        user = User.get_by_username(username)
        
        if user and user.check_password(form.password.data):
            # Login user
            login_user(user, remember=form.remember_me.data)
            
            # Update last access
            user.update_last_access()
            
            # Store user role in session
            session['user_role'] = user.rol
            session['user_name'] = user.nombre_completo
            
            flash(f'¡Bienvenido, {user.nombre_completo}!', 'success')
            
            # Redirigir según el rol del usuario
            next_page = request.args.get('next')
            if not next_page or not next_page.startswith('/'):
                # Use centralized redirect function
                next_page = get_redirect_for_role(user.rol)
            
            return redirect(next_page)
        else:
            flash('Usuario o contraseña incorrectos.', 'error')
    
    # Renderizar la plantilla con el formulario
    return render_template("login.html", form=form)

@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash('Has cerrado sesión exitosamente.', 'info')
    return redirect(url_for('auth.login'))

@auth_bp.route("/change-password")
@login_required
def change_password():
    # This is a placeholder - implementation can be added later
    return render_template("change_password.html")