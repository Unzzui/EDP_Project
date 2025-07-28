"""
Tenant Management API Routes.
Handles tenant creation, management, and onboarding.
"""
from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user
from datetime import datetime, timedelta
import secrets
import re

# Create blueprint
tenant_bp = Blueprint('tenant_api', __name__, url_prefix='/api/tenant')


@tenant_bp.route('/create', methods=['POST'])
def create_tenant():
    """
    Create a new tenant from landing page signup.
    
    Expected JSON:
    {
        "company_name": "ACME Corp",
        "contact_name": "John Doe",
        "contact_email": "john@acme.com",
        "contact_phone": "+56912345678",
        "plan_type": "starter"
    }
    """
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['company_name', 'contact_name', 'contact_email']
        for field in required_fields:
            if not data.get(field):
                return jsonify({
                    'success': False,
                    'message': f'Campo requerido: {field}'
                }), 400
        
        # Validate email format
        email = data['contact_email']
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
            return jsonify({
                'success': False,
                'message': 'Formato de email inválido'
            }), 400
        
        # Check if tenant already exists
        from ..models.tenant import Tenant
        existing_tenant = Tenant.query.filter_by(contact_email=email).first()
        if existing_tenant:
            return jsonify({
                'success': False,
                'message': 'Ya existe una empresa registrada con este email'
            }), 409
        
        # Create new tenant
        tenant = Tenant(
            company_name=data['company_name'],
            contact_name=data['contact_name'],
            contact_email=email,
            contact_phone=data.get('contact_phone'),
            plan_type=data.get('plan_type', 'starter')
        )
        
        # Save to master database
        from ..extensions import db
        db.session.add(tenant)
        db.session.commit()
        
        # Create tenant database
        tenant_db_manager = current_app.tenant_context.tenant_db_manager
        if not tenant_db_manager.create_tenant_database(tenant):
            # Rollback tenant creation if database creation fails
            db.session.delete(tenant)
            db.session.commit()
            return jsonify({
                'success': False,
                'message': 'Error creando base de datos de la empresa'
            }), 500
        
        # Send welcome email
        _send_welcome_email(tenant)
        
        return jsonify({
            'success': True,
            'message': 'Empresa creada exitosamente',
            'data': {
                'tenant_id': tenant.id,
                'company_slug': tenant.company_slug,
                'database_name': tenant.database_name,
                'trial_ends_at': tenant.trial_ends_at.isoformat(),
                'access_url': f"https://{tenant.company_slug}.pagora.com",
                'api_key': tenant.api_key
            }
        }), 201
        
    except Exception as e:
        current_app.logger.error(f"Error creating tenant: {e}")
        return jsonify({
            'success': False,
            'message': 'Error interno del servidor'
        }), 500


@tenant_bp.route('/<int:tenant_id>', methods=['GET'])
@login_required
def get_tenant(tenant_id):
    """Get tenant information."""
    try:
        from ..models.tenant import Tenant, TenantUser
        
        # Check if user has access to this tenant
        if not current_user.is_admin:
            tenant_user = TenantUser.query.filter_by(
                tenant_id=tenant_id,
                user_id=current_user.id
            ).first()
            if not tenant_user:
                return jsonify({
                    'success': False,
                    'message': 'No tienes acceso a esta empresa'
                }), 403
        
        tenant = Tenant.query.get_or_404(tenant_id)
        
        return jsonify({
            'success': True,
            'data': tenant.to_dict()
        })
        
    except Exception as e:
        current_app.logger.error(f"Error getting tenant {tenant_id}: {e}")
        return jsonify({
            'success': False,
            'message': 'Error interno del servidor'
        }), 500


@tenant_bp.route('/<int:tenant_id>/upgrade', methods=['POST'])
@login_required
def upgrade_tenant(tenant_id):
    """
    Upgrade tenant plan.
    
    Expected JSON:
    {
        "new_plan": "professional"  # or "enterprise"
    }
    """
    try:
        from ..models.tenant import Tenant, TenantUser
        from ..extensions import db
        
        data = request.get_json()
        new_plan = data.get('new_plan')
        
        if new_plan not in ['starter', 'professional', 'enterprise']:
            return jsonify({
                'success': False,
                'message': 'Plan inválido'
            }), 400
        
        # Check if user is owner of this tenant
        tenant_user = TenantUser.query.filter_by(
            tenant_id=tenant_id,
            user_id=current_user.id,
            is_owner=True
        ).first()
        
        if not tenant_user and not current_user.is_admin:
            return jsonify({
                'success': False,
                'message': 'Solo el propietario puede cambiar el plan'
            }), 403
        
        tenant = Tenant.query.get_or_404(tenant_id)
        old_plan = tenant.plan_type
        
        # Upgrade the plan
        tenant.upgrade_plan(new_plan)
        db.session.commit()
        
        # Log the change
        current_app.logger.info(f"Tenant {tenant.company_name} upgraded from {old_plan} to {new_plan}")
        
        return jsonify({
            'success': True,
            'message': f'Plan actualizado de {old_plan} a {new_plan}',
            'data': tenant.to_dict()
        })
        
    except Exception as e:
        current_app.logger.error(f"Error upgrading tenant {tenant_id}: {e}")
        return jsonify({
            'success': False,
            'message': 'Error interno del servidor'
        }), 500


@tenant_bp.route('/<int:tenant_id>/activate', methods=['POST'])
@login_required
def activate_subscription(tenant_id):
    """Activate paid subscription (end trial)."""
    try:
        from ..models.tenant import Tenant, TenantUser
        from ..extensions import db
        
        # Check if user is owner of this tenant
        tenant_user = TenantUser.query.filter_by(
            tenant_id=tenant_id,
            user_id=current_user.id,
            is_owner=True
        ).first()
        
        if not tenant_user and not current_user.is_admin:
            return jsonify({
                'success': False,
                'message': 'Solo el propietario puede activar la suscripción'
            }), 403
        
        tenant = Tenant.query.get_or_404(tenant_id)
        
        # Activate subscription
        tenant.activate_subscription()
        db.session.commit()
        
        current_app.logger.info(f"Subscription activated for tenant {tenant.company_name}")
        
        return jsonify({
            'success': True,
            'message': 'Suscripción activada exitosamente',
            'data': tenant.to_dict()
        })
        
    except Exception as e:
        current_app.logger.error(f"Error activating subscription for tenant {tenant_id}: {e}")
        return jsonify({
            'success': False,
            'message': 'Error interno del servidor'
        }), 500


@tenant_bp.route('/<int:tenant_id>/stats', methods=['GET'])
@login_required
def get_tenant_stats(tenant_id):
    """Get tenant database statistics."""
    try:
        from ..models.tenant import Tenant, TenantUser
        
        # Check if user has access to this tenant
        if not current_user.is_admin:
            tenant_user = TenantUser.query.filter_by(
                tenant_id=tenant_id,
                user_id=current_user.id
            ).first()
            if not tenant_user:
                return jsonify({
                    'success': False,
                    'message': 'No tienes acceso a esta empresa'
                }), 403
        
        tenant = Tenant.query.get_or_404(tenant_id)
        
        # Get database stats
        tenant_db_manager = current_app.tenant_context.tenant_db_manager
        stats = tenant_db_manager.get_tenant_stats(tenant)
        
        return jsonify({
            'success': True,
            'data': {
                'tenant_info': tenant.to_dict(),
                'database_stats': stats
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"Error getting stats for tenant {tenant_id}: {e}")
        return jsonify({
            'success': False,
            'message': 'Error interno del servidor'
        }), 500


@tenant_bp.route('/list', methods=['GET'])
@login_required
def list_tenants():
    """List all tenants (admin only) or user's tenants."""
    try:
        from ..models.tenant import Tenant, TenantUser
        
        if current_user.is_admin:
            # Admin can see all tenants
            tenants = Tenant.query.all()
        else:
            # Regular user can only see their tenants
            tenant_users = TenantUser.query.filter_by(user_id=current_user.id).all()
            tenant_ids = [tu.tenant_id for tu in tenant_users]
            tenants = Tenant.query.filter(Tenant.id.in_(tenant_ids)).all()
        
        return jsonify({
            'success': True,
            'data': [tenant.to_dict() for tenant in tenants]
        })
        
    except Exception as e:
        current_app.logger.error(f"Error listing tenants: {e}")
        return jsonify({
            'success': False,
            'message': 'Error interno del servidor'
        }), 500


def _send_welcome_email(tenant):
    """Send welcome email to new tenant."""
    try:
        from ..services.email_service import EmailService
        
        email_service = EmailService()
        
        subject = f"¡Bienvenido a PAGORA, {tenant.company_name}!"
        
        html_content = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h1 style="color: #00ff88;">¡Bienvenido a PAGORA!</h1>
            
            <p>Hola {tenant.contact_name},</p>
            
            <p>¡Gracias por registrar <strong>{tenant.company_name}</strong> en PAGORA!</p>
            
            <div style="background: #f5f5f5; padding: 20px; border-radius: 8px; margin: 20px 0;">
                <h3>Información de tu cuenta:</h3>
                <ul>
                    <li><strong>Empresa:</strong> {tenant.company_name}</li>
                    <li><strong>Plan:</strong> {tenant.plan_type.title()}</li>
                    <li><strong>Período de prueba:</strong> {tenant.days_left_in_trial} días restantes</li>
                    <li><strong>URL de acceso:</strong> https://{tenant.company_slug}.pagora.com</li>
                </ul>
            </div>
            
            <div style="background: #e6f3ff; padding: 20px; border-radius: 8px; margin: 20px 0;">
                <h3>Primeros pasos:</h3>
                <ol>
                    <li>Accede a tu panel usando la URL proporcionada</li>
                    <li>Inicia sesión con usuario: <strong>admin</strong> y contraseña: <strong>admin123</strong></li>
                    <li>Cambia tu contraseña en el primer acceso</li>
                    <li>Invita a tu equipo y comienza a gestionar tus EDPs</li>
                </ol>
            </div>
            
            <p>Si tienes alguna pregunta, no dudes en contactarnos en <a href="mailto:soporte@pagora.cl">soporte@pagora.cl</a></p>
            
            <p>¡Que tengas una excelente experiencia con PAGORA!</p>
            
            <p>
                Saludos,<br>
                El equipo de PAGORA
            </p>
        </div>
        """
        
        email_service.send_email(
            to_email=tenant.contact_email,
            subject=subject,
            html_content=html_content
        )
        
        current_app.logger.info(f"Welcome email sent to {tenant.contact_email}")
        
    except Exception as e:
        current_app.logger.error(f"Failed to send welcome email to {tenant.contact_email}: {e}")


# Register blueprint in your app factory
def register_tenant_routes(app):
    """Register tenant management routes."""
    app.register_blueprint(tenant_bp)
