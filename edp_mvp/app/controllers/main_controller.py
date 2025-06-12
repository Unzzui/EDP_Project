"""
Main Controller for the EDP Management System landing page and general routes.
"""

from flask import Blueprint, render_template, redirect, url_for, request
from flask_login import current_user, login_required
from datetime import datetime
from ..services.analytics_service import AnalyticsService

# Create Blueprint
main_bp = Blueprint("main", __name__)

# Initialize services
analytics_service = AnalyticsService()


@main_bp.route("/")
def index():
    """Landing page with overview statistics and navigation."""
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


@main_bp.route("/dashboard")
@login_required
def dashboard_redirect():
    """Redirect to appropriate dashboard based on user role."""
    # You can add role-based redirection here
    return redirect(url_for('controller.dashboard_controller'))


@main_bp.route("/about")
def about():
    """About page with system information."""
    return render_template("main/about.html")


@main_bp.route("/help")
@login_required
def help_page():
    """Help and documentation page."""
    return render_template("main/help.html")
