# app/auth/routes.py

from flask import Blueprint, render_template, redirect, url_for, request
from flask_login import login_user, logout_user, login_required, UserMixin, current_user
from app import login_manager
from .forms import LoginForm  # Import the form we just created

auth_bp = Blueprint("auth", __name__)

# Usuario de prueba (esto se simula ahora; luego se conecta a la base de usuarios real)
class User(UserMixin):
    def __init__(self, id, email=None):
        self.id = id
        self.email = email


# Esta función es requerida por Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return User(user_id)  # Cargar un usuario simulado por ahora

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    # Si el usuario ya está autenticado, redirigir al dashboard
    if current_user.is_authenticated:
        return redirect(url_for("controller_bp.dashboard_controller"))
    
    # Crear el formulario
    form = LoginForm()
    
    # Si el formulario se envía y valida
    if form.validate_on_submit():
        # Aquí implementarías la lógica de autenticación real
        # Por ahora, simulamos un login exitoso con un usuario de prueba
        user = User(id=1, email=form.email.data)
        login_user(user, remember=form.remember_me.data)
        
        # Redirigir a la página solicitada o al dashboard
        next_page = request.args.get('next')
        if not next_page or not next_page.startswith('/'):
            next_page = url_for('controller_bp.dashboard_controller')
        return redirect(next_page)
    
    # Renderizar la plantilla con el formulario
    return render_template("login.html", form=form)


@auth_bp.route("/logout")
def logout():
    return render_template("login.html")



@auth_bp.route("/change-password")
def change_password():
    # This is a placeholder - implementation can be added later
    return render_template("login.html")  # Replace with actual template when available