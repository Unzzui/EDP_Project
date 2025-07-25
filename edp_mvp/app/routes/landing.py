"""
Main Controller for the EDP Management System landing page and general routes.
"""

from flask import Blueprint, render_template, redirect, url_for, request
from flask_login import current_user, login_required
from datetime import datetime
from ..services.analytics_service import AnalyticsService

# Create Blueprint
landing_bp = Blueprint("landing", __name__)

# Initialize services
analytics_service = AnalyticsService()


@landing_bp.route("/")
def index():
    """Página de inicio principal que redirige según el rol del usuario."""
    if current_user.is_authenticated:
        # Redirigir según el rol del usuario
        user_role = getattr(current_user, 'rol', 'guest')
        
        if user_role == 'admin':
            return redirect(url_for('admin.dashboard'))
        elif user_role == 'manager':
            return redirect(url_for('management.dashboard'))
        elif user_role == 'controller':
            return redirect(url_for('dashboard.dashboard_controller'))
        elif user_role == 'jefe_proyecto':
            return redirect(url_for('projects.inicio'))
        else:
            return redirect(url_for('landing.dashboard_general'))
    
    # Si no está autenticado, mostrar página de bienvenida
    return render_template("main/welcome.html")


@landing_bp.route("/landing")
def landing():
    """Landing page original con estadísticas y información del sistema."""
    try:
        # Get basic statistics for the dashboard cards
        stats_response = analytics_service.get_basic_stats()
        
        stats = {
            'total_edps': 0,
            'monto_total': 0,
            'edps_pendientes': 0,
            'edps_criticos': 0,
            'tasa_aprobacion': 0
        }
        
        if stats_response.success and stats_response.data:
            stats = stats_response.data
        
        # Convert large numbers to readable format
        def format_number(num):
            if num >= 1_000_000_000:
                return f"${num/1_000_000_000:.1f}B"
            elif num >= 1_000_000:
                return f"${num/1_000_000:.1f}M"
            elif num >= 1_000:
                return f"${num/1_000:.1f}K"
            else:
                return f"${num:,.0f}"
        
        stats['monto_total_formatted'] = format_number(stats.get('monto_total', 0))
        
        return render_template(
            "main/landing.html",
            stats=stats,
            user=current_user,
            current_year=datetime.now().year
        )
        
    except Exception as e:
        print(f"Error in landing page: {e}")
        # Return basic template without stats on error
        return render_template(
            "main/landing.html",
            stats={'total_edps': 0, 'monto_total_formatted': '$0'},
            user=current_user,
            current_year=datetime.now().year
        )


@landing_bp.route("/dashboard")
@login_required
def dashboard_general():
    """Dashboard general para usuarios sin rol específico."""
    try:
        stats_response = analytics_service.get_basic_stats()
        stats = stats_response.data if stats_response.success else {}
        
        return render_template(
            "main/dashboard_general.html",
            stats=stats,
            current_date=datetime.now(),
            user=current_user,
            current_year=datetime.now().year
        )
    except Exception as e:
        print(f"Error in general dashboard: {e}")
        return render_template("main/dashboard_general.html", stats={}, current_date=datetime.now(), user=current_user)


@landing_bp.route("/dashboard/redirect")
@login_required
def dashboard_redirect():
    """Redirect to appropriate dashboard based on user role."""
    user_role = getattr(current_user, 'rol', 'guest')
    
    if user_role == 'admin':
        return redirect(url_for('admin.usuarios'))
    elif user_role == 'manager':
        return redirect(url_for('management.dashboard'))
    elif user_role == 'controller':
        return redirect(url_for('dashboard.dashboard_controller'))
    elif user_role == 'jefe_proyecto':
        return redirect(url_for('projects.inicio'))
    else:
        return redirect(url_for('landing.dashboard_general'))


@landing_bp.route("/about")
def about():
    """About page with system information."""
    return render_template("main/about.html")


@landing_bp.route("/help")
@login_required
def help_page():
    """Help and documentation page."""
    return render_template("main/help.html")
