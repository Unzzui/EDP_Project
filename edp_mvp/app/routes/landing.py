"""
Main Controller for the EDP Management System landing page and general routes.
"""

from flask import Blueprint, render_template, redirect, url_for, request, jsonify, flash
from flask_login import current_user, login_required
from datetime import datetime
from ..services.analytics_service import AnalyticsService

# Create Blueprint
landing_bp = Blueprint("landing", __name__)

# Initialize services
analytics_service = AnalyticsService()


@landing_bp.route("/")
def index():
    """Página de inicio principal que muestra el landing page."""
    # Mostrar siempre el landing page, independientemente del estado de autenticación
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
        
        # Si el usuario está autenticado y viene de una redirección de login_required,
        # mostrar un mensaje informativo
        next_page = request.args.get('next')
        if next_page and current_user.is_authenticated:
            flash(f'Para acceder a {next_page}, inicia sesión primero.', 'info')
        
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


@landing_bp.route("/landing")
def landing():
    """Landing page específico (mantenido para compatibilidad)."""
    # Esta ruta ahora es redundante ya que / muestra el landing
    # Se mantiene por compatibilidad con enlaces existentes
    return redirect(url_for('landing.index'))


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
        print(f"Error in dashboard general: {e}")
        return render_template(
            "main/dashboard_general.html",
            stats={},
            current_date=datetime.now(),
            user=current_user,
            current_year=datetime.now().year
        )


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


@landing_bp.route("/api/access-request", methods=["POST"])
def access_request():
    """Handle access request from landing page."""
    try:
        from ..services.email_service import EmailService
        
        data = request.get_json()
        
        if not data:
            return jsonify({
                "success": False,
                "message": "Datos requeridos"
            }), 400
        
        # Validate required fields
        required_fields = ['nombre', 'email', 'motivo']
        for field in required_fields:
            if not data.get(field):
                return jsonify({
                    "success": False,
                    "message": f"Campo requerido: {field}"
                }), 400
        
        # Prepare email content
        subject = "Nueva Solicitud de Acceso - PAGORA"
        
        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <h2 style="color: #0066cc;">Nueva Solicitud de Acceso - PAGORA</h2>
            <p>Se ha recibido una nueva solicitud de acceso al sistema PAGORA.</p>
            
            <h3 style="color: #0066cc;">Detalles del solicitante:</h3>
            <ul>
                <li><strong>Nombre:</strong> {data.get('nombre')}</li>
                <li><strong>Email:</strong> {data.get('email')}</li>
                <li><strong>Empresa:</strong> {data.get('empresa', 'No especificada')}</li>
                <li><strong>Cargo:</strong> {data.get('cargo', 'No especificado')}</li>
                <li><strong>Teléfono:</strong> {data.get('telefono', 'No especificado')}</li>
            </ul>
            
            <h3 style="color: #0066cc;">Motivo de la solicitud:</h3>
            <p style="background: #f5f5f5; padding: 15px; border-left: 4px solid #0066cc;">
                {data.get('motivo')}
            </p>
            
            <p><strong>Fecha de solicitud:</strong> {data.get('timestamp', 'No especificada')}</p>
            
            <hr style="margin: 20px 0;">
            <p style="font-size: 12px; color: #666;">
                Enviado desde el landing page de PAGORA
            </p>
        </body>
        </html>
        """
        
        text_body = f"""
        NUEVA SOLICITUD DE ACCESO - PAGORA
        
        Se ha recibido una nueva solicitud de acceso al sistema PAGORA.
        
        Detalles del solicitante:
        - Nombre: {data.get('nombre')}
        - Email: {data.get('email')}
        - Empresa: {data.get('empresa', 'No especificada')}
        - Cargo: {data.get('cargo', 'No especificado')}
        - Teléfono: {data.get('telefono', 'No especificado')}
        
        Motivo de la solicitud:
        {data.get('motivo')}
        
        Fecha de solicitud: {data.get('timestamp', 'No especificada')}
        
        ---
        Enviado desde el landing page de PAGORA
        """
        
        # Send email
        email_service = EmailService()
        recipients = ["diegobravobe@gmail.com"]
        
        success = email_service.send_email(subject, recipients, html_body, text_body)
        
        if success:
            return jsonify({
                "success": True,
                "message": "Solicitud enviada exitosamente"
            })
        else:
            return jsonify({
                "success": False,
                "message": "Error al enviar la solicitud. Inténtalo de nuevo."
            }), 500
            
    except Exception as e:
        print(f"Error en access request: {str(e)}")
        return jsonify({
            "success": False,
            "message": "Error interno del servidor"
        }), 500


@landing_bp.route("/api/contact", methods=["POST"])
def contact_form():
    """Handle contact form submissions from landing page."""
    try:
        from ..services.email_service import EmailService
        
        data = request.get_json()
        
        if not data:
            return jsonify({
                "success": False,
                "message": "Datos requeridos"
            }), 400
        
        # Validate required fields based on form type
        if data.get('tipo') == 'access-request':
            required_fields = ['nombre', 'email', 'motivo']
        else:
            required_fields = ['nombre', 'email', 'mensaje']
            
        for field in required_fields:
            if not data.get(field):
                return jsonify({
                    "success": False,
                    "message": f"Campo requerido: {field}"
                }), 400
        
        # Prepare email content based on form type
        if data.get('tipo') == 'access-request':
            subject = "Nueva Solicitud de Acceso - PAGORA"
            mensaje_content = data.get('motivo')
            form_type = "Solicitud de Acceso"
        else:
            subject = "Nuevo Mensaje de Contacto - PAGORA"
            mensaje_content = data.get('mensaje')
            form_type = "Formulario de Contacto"
        
        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <h2 style="color: #0066cc;">{form_type} - PAGORA</h2>
            <p>Se ha recibido un nuevo mensaje desde el landing page de PAGORA.</p>
            
            <h3 style="color: #0066cc;">Información del contacto:</h3>
            <ul>
                <li><strong>Nombre:</strong> {data.get('nombre')}</li>
                <li><strong>Email:</strong> {data.get('email')}</li>
                <li><strong>Empresa:</strong> {data.get('empresa', 'No especificada')}</li>
                <li><strong>Teléfono:</strong> {data.get('telefono', 'No especificado')}</li>
                {f"<li><strong>Cargo:</strong> {data.get('cargo', 'No especificado')}</li>" if data.get('cargo') else ""}
            </ul>
            
            <h3 style="color: #0066cc;">Mensaje:</h3>
            <p style="background: #f5f5f5; padding: 15px; border-left: 4px solid #0066cc;">
                {mensaje_content}
            </p>
            
            <p><strong>Fecha:</strong> {data.get('timestamp', 'No especificada')}</p>
            <p><strong>Tipo de formulario:</strong> {form_type}</p>
            
            <hr style="margin: 20px 0;">
            <p style="font-size: 12px; color: #666;">
                Enviado desde el landing page de PAGORA
            </p>
        </body>
        </html>
        """
        
        text_body = f"""
        {form_type.upper()} - PAGORA
        
        Se ha recibido un nuevo mensaje desde el landing page de PAGORA.
        
        Información del contacto:
        - Nombre: {data.get('nombre')}
        - Email: {data.get('email')}
        - Empresa: {data.get('empresa', 'No especificada')}
        - Teléfono: {data.get('telefono', 'No especificado')}
        {f"- Cargo: {data.get('cargo', 'No especificado')}" if data.get('cargo') else ""}
        
        Mensaje:
        {mensaje_content}
        
        Fecha: {data.get('timestamp', 'No especificada')}
        Tipo de formulario: {form_type}
        
        ---
        Enviado desde el landing page de PAGORA
        """
        
        # Send email
        email_service = EmailService()
        recipients = ["diegobravobe@gmail.com"]
        
        success = email_service.send_email(subject, recipients, html_body, text_body)
        
        if success:
            return jsonify({
                "success": True,
                "message": "Mensaje enviado exitosamente"
            })
        else:
            return jsonify({
                "success": False,
                "message": "Error al enviar el mensaje. Inténtalo de nuevo."
            }), 500
            
    except Exception as e:
        print(f"Error en contact form: {str(e)}")
        return jsonify({
            "success": False,
            "message": "Error interno del servidor"
        }), 500
